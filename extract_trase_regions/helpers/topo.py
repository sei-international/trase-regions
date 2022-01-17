import topojson as tp
import geopandas as gpd


def load_gdf_from_file(filename, crs="epsg:4326"):
    df = gpd.read_file(filename)
    df = df.set_crs(crs)
    return df


def gdf_to_topojson(gdf):
    return tp.Topology(gdf, prequantize=True).to_json()
