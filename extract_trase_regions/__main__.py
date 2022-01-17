from pathlib import Path
from argparse import ArgumentParser

from helpers.yaml import parse_yaml
from helpers.json import save_geojson_to_file, save_topojson_to_file
from helpers.topo import load_gdf_from_file, gdf_to_topojson
from helpers.db import run_sql_return_df
from helpers.queries import regions_dictionary_query, generate_geojson_query
from helpers.constants import (
    GEOJSON_EXTENSION,
    TOPOJSON_EXTENSION,
    COUNTRY_CODE_COL,
    COUNTRY_NAME_COL,
    LEVEL_COL,
)

OUT_FOLDER = 'data'

parser = ArgumentParser()
parser.add_argument("--country_codes", type=str, nargs="+", required=False,
                    help="Country codes to process, leave empty for all")

args = parser.parse_args()


def generate_filename(country_code, level):
    folder = f"{OUT_FOLDER}/{country_code.lower()}"
    Path(folder).mkdir(parents=True, exist_ok=True)
    return f"{folder}/{level}"


def extract_and_save_data(row):
    country_name = row[COUNTRY_NAME_COL]
    country_code = row[COUNTRY_CODE_COL]
    level = row[LEVEL_COL]
    print(f"---> {country_name}: getting level {level} data")
    result = run_sql_return_df(
                generate_geojson_query(country_name, level)
             ).iat[0, 0]  # get first row first column

    filename = generate_filename(country_code, level)
    # geojson
    save_geojson_to_file(result, filename)
    # topojson
    gdf = load_gdf_from_file(f'{filename}.{GEOJSON_EXTENSION}')
    topo = gdf_to_topojson(gdf)
    save_topojson_to_file(topo, filename)


def save_regions_metadata(df):
    df_tmp = df
    df_tmp["path_geojson"] = OUT_FOLDER + "/" + df[COUNTRY_CODE_COL].str.lower() + "/" + df[LEVEL_COL].astype(str) + f".{GEOJSON_EXTENSION}"
    df_tmp["path_topojson"] = OUT_FOLDER + "/" + df[COUNTRY_CODE_COL].str.lower() + "/" + df[LEVEL_COL].astype(str) + f".{TOPOJSON_EXTENSION}"
    df_tmp.to_json(f"{OUT_FOLDER}/metadata.json", orient="records", indent=4)


if __name__ == "__main__":
    countries_data = run_sql_return_df(regions_dictionary_query())
    save_regions_metadata(countries_data)
    if args.country_codes:
        countries_data = countries_data[countries_data[COUNTRY_CODE_COL].isin(args.country_codes)]
    print(f'---> regions to process {countries_data}')
    for index, row in countries_data.iterrows():
        try:
            extract_and_save_data(row)
        except Exception as e:
            print(f"---> error: {e}")
    print("---> all done.")
