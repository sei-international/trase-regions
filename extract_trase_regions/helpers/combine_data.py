import geopandas as gpd
import glob
from pathlib import Path
import pandas as pd

from helpers.json import save_topojson_to_file
from helpers.topo import gdf_to_topojson


def combine_data(level, OUT_FOLDER):
    print(f"---> combining data for level: {level}")
    files = glob.glob(f"{OUT_FOLDER}/**/{level}.geojson")
    print(f"---> files found {files}")
    frames = [gpd.read_file(f) for f in files]
    df = gpd.GeoDataFrame(pd.concat(frames))
    df = df.set_crs("epsg:4326")
    folder = f"{OUT_FOLDER}/all"
    Path(folder).mkdir(parents=True, exist_ok=True)
    filename = f"{folder}/{level}"
    print(f"---> saving to {filename}")
    df.to_file(f"{filename}.geojson", driver="GeoJSON")

    topo = gdf_to_topojson(df)
    save_topojson_to_file(topo, f"{filename}.topo.json")
