import geopandas as gpd
import pandas as pd
import pyproj
from helpers.constants import GEOJSON_EXTENSION
from helpers.db import run_sql_return_df
from helpers.files import generate_filename, write_topojson
from shapely.ops import transform

SHAPEFILE_3_0_PATH = "/tmp/ID_pulpwood_concessions_3_0.shp"  # 2015-2019
SHAPEFILE_3_1_PATH = "/tmp/ID_pulpwood_concessions_3_1.shp"  # 2020-2022
SHAPEFILE_3_2_PATH = "/tmp/ID_pulpwood_concessions_3_2.shp"  # 2023-2024
INDONESIA_BOUNDS = {
    # Bounding box for Indonesia (EPSG:4326), slightly buffered.
    # Approx. 95°E to 141°E, 6°N to 11°S
    "min_lon": 94.9,
    "max_lon": 141.1,
    "min_lat": -11.1,
    "max_lat": 6.1,
}


def check_bounds(geom):
    minx, miny, maxx, maxy = geom.bounds
    return (
        minx >= INDONESIA_BOUNDS["min_lon"]
        and maxx <= INDONESIA_BOUNDS["max_lon"]
        and miny >= INDONESIA_BOUNDS["min_lat"]
        and maxy <= INDONESIA_BOUNDS["max_lat"]
    )


def read_shapefile(path, name_column, province_code_column):
    """
    Reads a shapefile using GeoPandas, reprojects row-by-row
    to handle NULL geometries, and returns a GeoDataFrame ready
    for GeoJSON export.
    """
    # 1. Read the file
    gdf = gpd.read_file(path)
    src_crs = gdf.crs
    target_crs = "EPSG:4326"

    # Set up the transformer for reprojection
    transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)

    def process_geom(geom):
        """
        Reprojects a single geometry. Returns None if the geometry is null or empty.
        """
        if geom is None or geom.is_empty:
            return None  # Propagate None for null geometries

        # Reproject
        try:
            # The output of transform is a Shapely geometry object
            reprojected_geom = transform(transformer.transform, geom)
            return reprojected_geom
        except Exception as e:
            # It's generally better to log the error and return None/a placeholder
            print(f"ERROR reprojecting geometry: {e}")
            return None

    # Create the output GeoDataFrame, using the original geometry column initially
    gdf_out = gdf[["geometry", "ID", name_column, province_code_column]].copy()

    # Reproject the geometry column
    # This overwrites the original geometry column with the reprojected, or None
    gdf_out["geometry"] = gdf["geometry"].apply(process_geom)

    # Set the CRS of the new geometry column explicitly
    gdf_out.crs = target_crs

    # check no null geometry
    assert gdf_out["geometry"].notnull().all()

    # assert all points are inside Indonesia - this tests our reprojection worked
    is_in_indonesia = gdf_out["geometry"].apply(check_bounds).fillna(True)
    assert all(is_in_indonesia)

    # Rename columns
    gdf_out = gdf_out.rename(
        columns={
            "ID": "id",
            name_column: "name",
            province_code_column: "province_code",
        },
        errors="raise",
    )

    gdf_out["province_code"] = pd.to_numeric(
        gdf_out["province_code"], errors="coerce"
    ).astype("Int64")

    return gdf_out


def process_concessions(df, df_provinces, names: dict):
    trase_id = "ID-WOOD-CONCESSION-" + df["id"].str.replace("H-", "")
    new_columns = {
        "trase_id": trase_id,
        "biome": None,
        "country": "INDONESIA",
        "node_type_name": "Wood pulp concession",
        "node_type_slug": "wood-pulp-concession",
        "parent_node_type_name": "Province",
    }
    df = df.assign(**new_columns)

    # fix concession names
    new_names = df["trase_id"].map(names)
    assert new_names.notnull().all(), "Missing some names!"
    df["name"] = new_names

    # add province (parent) names
    df = pd.merge(
        df,
        df_provinces[["province_code", "parent_name"]],
        on="province_code",
        validate="many_to_one",
        how="left",
    )
    assert not any(df["parent_name"].isnull()), "Could not find some provinces"

    return df[[*new_columns.keys(), "name", "parent_name", "geometry"]]


def write_data(df, filename):
    df = df.assign(id=df["trase_id"])
    df.to_file(
        f"{filename}.{GEOJSON_EXTENSION}",
        driver="GeoJSON",
        layer_options={"ID_FIELD": "id"},
    )
    print(f"---> saving {filename}.{GEOJSON_EXTENSION}")

    write_topojson(filename)


def write_indonesia_concessions():
    # read province codes and names
    df_provinces = run_sql_return_df(
        """
        SELECT 
            SUBSTR(trase_id, 4)::int AS province_code
            , name AS parent_name
        FROM main.nodes
        JOIN main.node_names ON nodes.id = node_names.node_id
        WHERE node_names.is_default AND nodes.trase_id ~ '^ID-[0-9]{2}$'
        """
    )

    # read chosen frontend names for concessions
    df_names = pd.read_csv(
        "s3://trase-storage/indonesia/wood_pulp/companies/align_names/ALIGNED_NAMES_HTI_V2025.csv",
        usecols=["ID", "CONC_FRONTEND"],
    )
    names = {trase_id: name for (_, trase_id, name) in df_names.itertuples()}

    # read concessions data
    filename = generate_filename("ID", "wood-pulp-concession")

    d = read_shapefile(SHAPEFILE_3_0_PATH, "NAMOBJ", "Kode_Prov")
    df_3_0 = process_concessions(d, df_provinces, names)
    write_data(df_3_0, filename + "-2019")

    d = read_shapefile(SHAPEFILE_3_1_PATH, "namaobj", "kode_prov")
    df_3_1 = process_concessions(d, df_provinces, names)
    write_data(df_3_1, filename + "-2020")

    d = read_shapefile(SHAPEFILE_3_2_PATH, "namobj", "kode_prov")
    df_3_2 = process_concessions(d, df_provinces, names)
    write_data(df_3_2, filename + "-2023")


if __name__ == "__main__":
    write_indonesia_concessions()
