import json
import os
import time

import geopandas as gpd
import pandas as pd
import requests
from shapely import wkt

# --- Ayarlar ---
POLYGON_PATH = "data/poligon.json"
OUTPUT_FOLDER = "data/osm_results"
BUFFER_METERS = 250
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def safe_wkt_load(val):
    try:
        return wkt.loads(val)
    except:
        return None


def download_osm_data(lat, lon, radius=250, tags=("building", "highway")):
    tag_filters = "".join(
        [
            f'node["{tag}"](around:{radius},{lat},{lon});way["{tag}"](around:{radius},{lat},{lon});relation["{tag}"](around:{radius},{lat},{lon});'
            for tag in tags
        ]
    )
    query = f"""
    [out:json][timeout:25];
    (
      {tag_filters}
    );
    out body;
    >;
    out skel qt;
    """
    response = requests.post(OVERPASS_URL, data={"data": query})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Hata: {response.status_code}")
        return None


# --- Poligonları Yükle ---
with open(POLYGON_PATH, "r") as f:
    raw = json.load(f)
df = pd.DataFrame(raw)
df["geometry"] = df["geometry"].apply(safe_wkt_load)
df = df[df["geometry"].notnull()]
gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:3857")
gdf_latlon = gdf.to_crs(epsg=4326)

# --- Her poligonun merkezi için OSM verisi indir ---
downloaded = 0
for idx, row in gdf_latlon.iterrows():
    poly_id = row["ID"]
    centroid = row.geometry.centroid
    lat, lon = centroid.y, centroid.x
    save_path = os.path.join(OUTPUT_FOLDER, f"{poly_id}_osm.json")

    if os.path.exists(save_path):
        continue

    print(f"⬇️ {poly_id} için veri indiriliyor... ({lat:.5f}, {lon:.5f})")
    data = download_osm_data(lat, lon, radius=BUFFER_METERS)
    if data:
        with open(save_path, "w") as f:
            json.dump(data, f)
        downloaded += 1
    time.sleep(1)

print(f"✅ İşlem tamamlandı. Yeni indirilen dosya sayısı: {downloaded}")
