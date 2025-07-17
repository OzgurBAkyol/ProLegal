import json
import math
import os
from time import sleep

import geopandas as gpd
import pandas as pd
import requests
from dotenv import load_dotenv
from shapely import wkt
from shapely.errors import WKTReadingError

# 1. API Key yükle
load_dotenv()
API_KEY = os.getenv("GOOGLE_ELEVATION_API_KEY")
print("🔑 Yüklenen API KEY:", "OK" if API_KEY else "❌ Bulunamadı")


# 2. WKT düzeltici ((())) -> (())
def fix_wkt(wkt_str):
    if not wkt_str or not isinstance(wkt_str, str):
        return None
    for _ in range(5):
        try:
            return wkt.loads(wkt_str)
        except WKTReadingError:
            if wkt_str.startswith("(") and wkt_str.endswith(")"):
                wkt_str = wkt_str[1:-1]
            else:
                break
    return None


# 3. Google Elevation API çağrısı
def get_elevation(lat, lon):
    url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lon}&key={API_KEY}"
    try:
        sleep(0.2)
        response = requests.get(url)
        print(f"🌍 API çağrısı: {url}")
        response.raise_for_status()
        result = response.json()
        if result["status"] != "OK":
            print(
                f"⚠️ Google API Hatası: {result['status']} - {result.get('error_message', '')}"
            )
            return None
        return result["results"][0]["elevation"]
    except Exception as e:
        print(f"❌ API çağrısı başarısız: {e}")
        return None


# 4. Eğim hesapla
def compute_slope(lat, lon):
    delta = 0.0005
    points = [
        (lat, lon),
        (lat + delta, lon),
        (lat - delta, lon),
        (lat, lon + delta),
        (lat, lon - delta),
    ]
    elevations = [get_elevation(y, x) for y, x in points]
    if None in elevations:
        print("⚠️ Elevation verilerinde eksik var. Skipping...")
        return None
    center = elevations[0]
    diffs = [(abs(e - center)) / 55.0 for e in elevations[1:]]
    slope_rad = [math.atan(d / 1.0) for d in diffs]
    slope_deg = [round(math.degrees(s), 1) for s in slope_rad]
    return round(sum(slope_deg) / len(slope_deg), 1)


# 5. Ana script
def main():
    os.makedirs("data/slope", exist_ok=True)
    out_path = "data/slope/slope_cache.csv"

    with open("data/poligon.json") as f:
        raw = json.load(f)

    df = pd.DataFrame(raw)
    df["geometry"] = df["geometry"].apply(fix_wkt)
    df = df[df["geometry"].notnull()]
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:3857").to_crs("EPSG:4326")

    # Eğer dosya varsa daha önce yazılmış ID'leri oku (isteğe bağlı optimize)
    if os.path.exists(out_path):
        done_ids = set(pd.read_csv(out_path)["ID"])
    else:
        done_ids = set()

    with open(out_path, "a", encoding="utf-8", newline="") as f_out:
        for idx, row in gdf.iterrows():
            poly_id = row.get("ID", f"poly_{idx}")
            if poly_id in done_ids:
                continue

            centroid = row.geometry.centroid
            print(f"\n--- Poligon {idx} ---")
            print(f"📌 ID: {poly_id}")
            print(f"📍 Centroid: {centroid.y:.6f}, {centroid.x:.6f}")

            slope = compute_slope(centroid.y, centroid.x)
            print(f"📈 Eğim (°): {slope}")

            pd.DataFrame([{"ID": poly_id, "Eğim (°)": slope}]).to_csv(
                f_out, header=not f_out.tell(), index=False
            )

    print(f"\n✅ Tüm veriler eklendi: {out_path}")


if __name__ == "__main__":
    main()


# 	1.	Başlangıç Noktası (Merkez/Centroid):
# 	•	Her poligonun ağırlık merkezi (centroid) alınıyor → lat, lon
# 	2.	5 Adet Nokta Seçiliyor (yaklaşık 55 metre çevresinden):
#   3.	Google Elevation API ile Rakım Verisi Alınıyor:
# 	•	Her nokta için yükseklik alınır → get_elevation()
# 	•	5 yükseklik verisi elde edilir: [center, north, south, east, west]
# 	4.	Yükseklik Farklarından Eğim Hesaplanır:
# 	•	Merkez ile çevresindeki 4 nokta arasındaki yükseklik farkı alınır.
# 	•	55 metre yatay mesafeye karşılık gelen eğim (tanjant) hesaplanır.
# 	•	math.atan() ile eğim açısına dönüştürülür.
# 	•	math.degrees() ile dereceye çevrilir.
# 	•	Ortalama eğim alınır:
