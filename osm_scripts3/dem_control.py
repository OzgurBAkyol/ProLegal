import json
import os

import geopandas as gpd
import numpy as np
import rasterio
import rasterio.mask
from shapely import wkt
from shapely.errors import WKTReadingError


# Fazladan parantezleri kaldırarak WKT düzeltici
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


# JSON'dan tüm polygonları yükle
with open("data/poligon.json") as f:
    data = json.load(f)
df = gpd.GeoDataFrame(data)
df["geometry"] = df["geometry"].apply(lambda x: fix_wkt(x))
df = df[df["geometry"].notnull()]
df = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:3857")

# Tüm TIF'leri indexle
tif_index = []
tif_dir = "data/elevation"
for file in os.listdir(tif_dir):
    if file.endswith(".tif") and not file.startswith("dem_merged"):
        path = os.path.join(tif_dir, file)
        with rasterio.open(path) as src:
            tif_index.append(
                {
                    "file": path,
                    "bounds": src.bounds,
                    "crs": src.crs,
                    "nodata": src.nodata,
                    "res": src.res,
                }
            )

# Poligonları sırayla test et
for i, poly in enumerate(df.geometry[:20]):  # ilk 20 poligonu dene
    print(f"\n--- Poligon {i} ---")
    print(f"🧩 EPSG:3857 Bounds: {poly.bounds}")

    centroid = (
        gpd.GeoSeries([poly], crs="EPSG:3857")
        .to_crs("EPSG:4326")
        .geometry.centroid.iloc[0]
    )
    print(f"📍 Centroid: {centroid.x:.4f}, {centroid.y:.4f}")

    match = None
    for tif in tif_index:
        left, bottom, right, top = tif["bounds"]
        if left <= centroid.x <= right and bottom <= centroid.y <= top:
            match = tif
            break

    if not match:
        print("❌ Uyumlu TIF bulunamadı.")
        continue

    print(f"✅ Eşleşen TIF: {os.path.basename(match['file'])}")
    try:
        with rasterio.open(match["file"]) as src:
            poly4326 = (
                gpd.GeoSeries([poly], crs="EPSG:3857").to_crs(src.crs).geometry.iloc[0]
            )
            out_image, _ = rasterio.mask.mask(
                src, [poly4326.__geo_interface__], crop=True
            )
            elevation = out_image[0].astype("float32")

            nodata = src.nodata if src.nodata is not None else -32768
            elevation[elevation == nodata] = np.nan

            print(f"📏 Raster res: {src.res}, shape: {elevation.shape}")
            print(
                f"📊 Elevation Min: {np.nanmin(elevation)}, Max: {np.nanmax(elevation)}"
            )
            print(f"🕳️ NaN oranı: {np.isnan(elevation).mean()*100:.2f}%")

            if np.isnan(elevation).all():
                print("⚠️ Tüm değerler NaN.")
            else:
                x, y = np.gradient(elevation, src.res[0], src.res[1])
                slope = np.degrees(np.arctan(np.sqrt(x**2 + y**2)))
                print(f"📈 Ortalama eğim: {round(np.nanmean(slope), 1)}°")
                print(f"📉 Median eğim: {round(np.nanmedian(slope), 1)}°")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
