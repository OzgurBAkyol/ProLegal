import json
import os
import re
import time

import pyproj
import requests
from requests.adapters import HTTPAdapter
from shapely import wkt
from shapely.errors import WKTReadingError
from shapely.geometry import Polygon
from shapely.ops import transform
from tqdm import tqdm
from urllib3.util.retry import Retry

# 📁 Dosya yolları
POLYGON_FILE = "data/poligon.json"
OUTPUT_FOLDER = "data/osm_results"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🌐 Koordinat dönüşüm: EPSG:3857 → EPSG:4326
project = pyproj.Transformer.from_crs(
    "EPSG:3857", "EPSG:4326", always_xy=True
).transform

# 🌍 Overpass API session (retry & timeout destekli)
session = requests.Session()
retry_strategy = Retry(
    total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)


# 🧽 Fazla parantezleri düzelt
def clean_wkt(wkt_str):
    if wkt_str.strip().startswith("POLYGON"):
        wkt_str = re.sub(r"POLYGON\s*\(\(\((.+?)\)\)\)", r"POLYGON ((\1))", wkt_str)
    return wkt_str


# 🔧 Geometriyi düzelt
def fix_geometry(wkt_str):
    try:
        cleaned = clean_wkt(wkt_str)
        geom = wkt.loads(cleaned)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if isinstance(geom, Polygon):
            return geom.wkt
    except Exception:
        return None


# 📌 Poligon merkezini ve yarıçapını bul
def get_center_and_radius(wkt_str):
    try:
        geom_3857 = wkt.loads(wkt_str)
        if geom_3857.is_empty or not geom_3857.is_valid:
            raise ValueError("Geometri boş veya geçersiz.")
        geom_4326 = transform(project, geom_3857)
        center = geom_4326.centroid
        radius_m = (
            max(
                geom_4326.bounds[2] - geom_4326.bounds[0],
                geom_4326.bounds[3] - geom_4326.bounds[1],
            )
            * 111000
            / 2
        )
        return center.y, center.x, int(radius_m)
    except Exception as e:
        raise ValueError(f"Geometri dönüşüm hatası: {e}")


# 🏗 Overpass API'den bina verisi çek
def fetch_buildings(lat, lon, radius):
    query = f"""
    [out:json][timeout:25];
    (
      way["building"](around:{radius},{lat},{lon});
      relation["building"](around:{radius},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """
    url = "https://overpass-api.de/api/interpreter"
    try:
        response = session.post(url, data={"data": query}, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise RuntimeError(f"Overpass isteği başarısız: {e}")


# 🔁 Ana döngü
with open(POLYGON_FILE) as f:
    polygons = json.load(f)

for i, poly in enumerate(tqdm(polygons, desc="🔽 Bina Verileri İndiriliyor")):
    poly_id = poly.get("ID")
    wkt_raw = poly.get("geometry")

    if not poly_id or not wkt_raw:
        print(f"[!] Geçersiz veri atlandı. Index: {i}")
        continue

    out_path = os.path.join(OUTPUT_FOLDER, f"{poly_id}_buildings.json")
    if os.path.exists(out_path):
        continue

    # 🧼 Geometriyi düzelt
    fixed_wkt = fix_geometry(wkt_raw)
    if not fixed_wkt:
        print(f"[X] {poly_id} WKT düzeltilemedi.")
        with open("errors.log", "a") as log:
            log.write(f"{poly_id} - WKT düzeltilemedi\n")
        continue

    try:
        lat, lon, radius = get_center_and_radius(fixed_wkt)
        data = fetch_buildings(lat, lon, radius)

        # ❌ Eğer bina verisi yoksa dosya yazma
        if not data.get("elements"):
            print(f"[ ] {poly_id} için bina bulunamadı.")
            continue

        with open(out_path, "w") as f_out:
            json.dump(data, f_out)

    except (WKTReadingError, ValueError) as we:
        print(f"[X] {poly_id} WKT hatası: {we}")
        with open("errors.log", "a") as log:
            log.write(f"{poly_id} - WKT: {we}\n")
    except Exception as e:
        print(f"[X] {poly_id} API hatası: {e}")
        with open("errors.log", "a") as log:
            log.write(f"{poly_id} - API: {e}\n")

    time.sleep(2)

print("✅ Tüm bina verileri indirildi.")
