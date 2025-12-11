import json
from helpers.constants import GEOJSON_EXTENSION


def save_geojson_to_file(data, filename):
    filename += f".{GEOJSON_EXTENSION}"
    print(f"---> saving {filename}")
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False)

