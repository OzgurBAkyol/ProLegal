import os
import subprocess
from time import sleep

from osgeo import gdal

# 📁 Klasör hazırlığı
elevation_dir = "data/elevation"
os.makedirs(elevation_dir, exist_ok=True)

# 📌 Türkiye sınırlarında 2x2 derecelik dilimler
lon_ranges = [(lon, lon + 2) for lon in range(25, 45, 2)]
lat_ranges = [(lat, lat + 2) for lat in range(35, 43, 2)]

downloaded_files = []

# ⬇️ DEM tile'larını indir
for lon_min, lon_max in lon_ranges:
    for lat_min, lat_max in lat_ranges:
        out_tif = f"{elevation_dir}/dem_{lon_min}_{lat_min}.tif"
        if os.path.exists(out_tif):
            print(f"✅ Zaten var: {out_tif}")
            downloaded_files.append(out_tif)
            continue

        print(f"⬇️ İndiriliyor: {out_tif}")
        try:
            subprocess.run(
                [
                    "eio",
                    "clip",
                    "-o",
                    out_tif,
                    "--bounds",
                    str(lon_min),
                    str(lat_min),
                    str(lon_max),
                    str(lat_max),
                ],
                check=True,
            )
            if os.path.exists(out_tif):
                downloaded_files.append(out_tif)
            else:
                print(f"[X] Dosya oluşturulamadı: {out_tif}")
        except subprocess.CalledProcessError as e:
            print(f"[X] Hata oluştu: {e}")
        sleep(1)

# 🧩 Merge işlemi
merged_path = f"{elevation_dir}/dem.tif"
if downloaded_files:
    print(f"\n🧩 {len(downloaded_files)} dosya birleştiriliyor → {merged_path}")
    try:
        subprocess.run(
            ["gdal_merge.py", "-o", merged_path, "-of", "GTiff"] + downloaded_files,
            check=True,
        )
        print("✅ Merge tamamlandı.")
    except subprocess.CalledProcessError:
        print("❌ Merge başarısız.")
else:
    print("⚠️ Hiçbir dosya indirilemedi.")
    exit(1)

# ⛰️ Eğim (slope) hesapla
slope_path = f"{elevation_dir}/slope.tif"
print(f"\n📐 Eğim hesaplanıyor → {slope_path}")
gdal.DEMProcessing(slope_path, merged_path, "slope", format="GTiff")
print("✅ Eğim raster'ı oluşturuldu.")
