from pathlib import Path
from argparse import ArgumentParser
import json

from helpers.yaml import parse_yaml
from helpers.json import save_geojson_to_file, save_topojson_to_file
from helpers.topo import load_gdf_from_file, gdf_to_topojson
from helpers.db import run_sql_return_df
from helpers.queries import regions_dictionary_query, generate_geojson_query
from helpers.combine_data import combine_data
from helpers.constants import (
    OUT_FOLDER,
    GEOJSON_EXTENSION,
    TOPOJSON_EXTENSION,
    COUNTRY_CODE_COL,
    COUNTRY_NAME_COL,
    LEVEL_COL,
    REPO_FILES_URL,
)

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
    print(generate_geojson_query(country_name, level))
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
    base_path = f"{REPO_FILES_URL}/{OUT_FOLDER}/"
    df_tmp["path_geojson"] = base_path + df[COUNTRY_CODE_COL].str.lower() + "/" + df[LEVEL_COL].astype(str) + f".{GEOJSON_EXTENSION}"
    df_tmp["path_topojson"] = base_path + df[COUNTRY_CODE_COL].str.lower() + "/" + df[LEVEL_COL].astype(str) + f".{TOPOJSON_EXTENSION}"
    # need to do the following so pandas won't escape forward slashes in URLs
    out = df_tmp.to_json(orient="records")
    with open(f"{OUT_FOLDER}/metadata.json", "w") as f:
        json.dump(json.loads(out), f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    print("---> getting metadata for all regions")
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
    levels = countries_data.level.unique()
    print(f"---> combining data for each level into a single file")
    for level in levels:
        combine_data(level, OUT_FOLDER)
    print("---> all done.")
