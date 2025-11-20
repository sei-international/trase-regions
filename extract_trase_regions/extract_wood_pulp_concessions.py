import pandas as pd
import geopandas as gpd
import pyproj
from shapely.ops import transform

from helpers.constants import GEOJSON_EXTENSION
from helpers.files import generate_filename, write_topojson
from helpers.db import run_sql_return_df

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

    # 2. Select, Rename, and Reproject
    # Create the output GeoDataFrame, using the original geometry column initially
    gdf_out = gdf[["geometry", "ID", name_column, province_code_column]].copy()

    # Reproject the geometry column
    # This overwrites the original geometry column with the reprojected, or None
    gdf_out["geometry"] = gdf["geometry"].apply(process_geom)

    # Set the CRS of the new geometry column explicitly
    gdf_out.crs = target_crs

    # Rename columns
    gdf_out = gdf_out.rename(
        columns={
            "ID": "id",
            name_column: "name",
            province_code_column: "province_code",
        },
        errors="raise",
    )

    # 3. Clean up data (province code cast)
    # Ensure any rows where geometry failed/is null are kept if data is needed
    gdf_out["province_code"] = pd.to_numeric(gdf_out["province_code"], errors='coerce').astype('Int64')

    # check no null geometry
    assert gdf_out["id"].notnull().all()

    return gdf_out


def append_missing(df1, df2):
    existing_ids = set(df1["id"])
    missing_rows = df2[~df2["id"].isin(existing_ids)]
    return pd.concat([df1, missing_rows], ignore_index=True)


def coordinates(geojson_dictionary):
    _type = geojson_dictionary.get("type")
    coordinates = geojson_dictionary.get("coordinates", [])
    if _type == "MultiPolygon":
        for polygon in coordinates:
            for ring in polygon:
                for lon, lat in ring:
                    yield lon, lat
    elif _type == "Polygon":
        for ring in coordinates:
            for lon, lat in ring:
                yield lon, lat
    else:
        raise NotImplementedError(f"Cannot support {_type}")


def is_in_indonesia(lon, lat):
    return (INDONESIA_BOUNDS["min_lon"] <= lon <= INDONESIA_BOUNDS["max_lon"]) and (
        INDONESIA_BOUNDS["min_lat"] <= lat <= INDONESIA_BOUNDS["max_lat"]
    )


def process_concessions(df, df_provinces):
    df["id"] = "ID-WOOD-CONCESSION-" + df['id'].str.replace('H-', '')
    df["biome"] = None
    df["country"] = "INDONESIA"
    df["node_type_name"] = "Wood pulp concession"
    df["node_type_slug"] = "wood-pulp-concession"
    df["parent_node_type_name"] = "Province"

    # add province (parent) names
    df = pd.merge(
        df,
        df_provinces[["province_code", "parent_name"]],
        on="province_code",
        validate="many_to_one",
        how="left"
    )
    assert not any(df["parent_name"].isnull()), "Could not find some provinces"

    return df[[
        "id",
        "biome",
        "name",
        "country",
        "parent_name",
        "node_type_name",
        "node_type_slug",
        "parent_node_type_name",
        "geometry",
    ]]


def write_data(df, filename):
    df.to_file(f"{filename}.{GEOJSON_EXTENSION}", driver="GeoJSON")
    print(f"---> saving {filename}.{GEOJSON_EXTENSION}")

    write_topojson(filename)


def write_indonesia_concessions():
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

    filename = generate_filename("id", "wood-pulp-concession")

    d = read_shapefile(SHAPEFILE_3_0_PATH, "NAMOBJ", "Kode_Prov")
    df_3_0 = process_concessions(d, df_provinces)
    write_data(df_3_0, filename + "-2019")

    d = read_shapefile(SHAPEFILE_3_1_PATH, "namaobj", "kode_prov")
    df_3_1 = process_concessions(d, df_provinces)
    write_data(df_3_1, filename + "-2020")

    d = read_shapefile(SHAPEFILE_3_2_PATH, "namobj", "kode_prov")
    df_3_2 = process_concessions(d, df_provinces)
    write_data(df_3_2, filename + "-2023")


if __name__ == "__main__":
    write_indonesia_concessions()