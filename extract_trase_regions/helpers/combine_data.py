import geopandas as gpd
import glob
from pathlib import Path
import pandas as pd
from helpers.constants import (
    GEOJSON_EXTENSION,
)


def combine_data(level, OUT_FOLDER):
    print(f"---> combining data for level: {level}")
    files = [
        f for f in glob.glob(f"{OUT_FOLDER}/**/{level}*.{GEOJSON_EXTENSION}")
        if "/all/" not in f  # ignore /all/ folder files
    ]
    print(f"---> files found {files}")
    frames = [gpd.read_file(f) for f in files]

    if not frames:
        raise RuntimeError(f"---> no files found for level {level}, unable to combine")

    df = gpd.GeoDataFrame(pd.concat(frames))
    df = df.set_crs("epsg:4326")
    folder = f"{OUT_FOLDER}/all"
    Path(folder).mkdir(parents=True, exist_ok=True)
    filename = f"{folder}/{level}"
    print(f"---> saving to {filename}")
    df.to_file(f"{filename}.{GEOJSON_EXTENSION}", driver="GeoJSON")
