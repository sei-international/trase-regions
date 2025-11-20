from pathlib import Path

from helpers.constants import OUT_FOLDER, GEOJSON_EXTENSION
from helpers.json import save_topojson_to_file
from helpers.topo import load_gdf_from_file, gdf_to_topojson


def generate_filename(country_code, level):
    folder = f"{OUT_FOLDER}/{country_code.lower()}"
    Path(folder).mkdir(parents=True, exist_ok=True)
    return f"{folder}/{level}"


def write_topojson(filename):
    gdf = load_gdf_from_file(f'{filename}.{GEOJSON_EXTENSION}')
    topo = gdf_to_topojson(gdf)
    save_topojson_to_file(topo, filename)
