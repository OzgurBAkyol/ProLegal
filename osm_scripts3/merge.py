import os
import subprocess

# 📁 DEM klasörü ve çıktı dosyası
elevation_dir = "data/elevation"
merged_output = os.path.join(elevation_dir, "dem_merged.tif")

# 📄 dem_*.tif dosyalarını listele
tif_files = sorted(
    [
        os.path.join(elevation_dir, f)
        for f in os.listdir(elevation_dir)
        if f.startswith("dem_") and f.endswith(".tif") and f != "dem_merged.tif"
    ]
)

# 🔍 Kontrol
print(f"{len(tif_files)} dosya bulundu, birleştiriliyor...")

# 🧩 Merge işlemi
try:
    subprocess.run(
        ["gdal_merge.py", "-o", merged_output, "-of", "GTiff"] + tif_files, check=True
    )
    print(f"✅ Merge işlemi tamamlandı → {merged_output}")
except subprocess.CalledProcessError as e:
    print(f"❌ Merge sırasında hata oluştu: {e}")
