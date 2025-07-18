import requests
import pandas as pd
import os

# 📌 Urla ilçe ID'si
ILCE_ID = 563
URL = f"https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api/idariYapi/mahalleListe/{ILCE_ID}"

response = requests.get(URL)

if response.status_code == 200:
    data = response.json()
    features = data.get("features", [])

    print(f"\n📍 Urla Mahalleleri (Toplam: {len(features)}):")
    mahalleler = []
    for mahalle in features:
        props = mahalle.get("properties", {})
        mahalle_adi = props.get("text")
        mahalle_id = props.get("id")
        mahalleler.append({"MahalleAdı": mahalle_adi, "MahalleID": mahalle_id})
        print(f"- {mahalle_adi} (ID: {mahalle_id})")

    # 💾 CSV olarak kaydet
    df = pd.DataFrame(mahalleler)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/mahalle_id.csv", index=False, encoding="utf-8")
    print("\n✅ Kayıt tamamlandı → data/mahalle_id.csv")
else:
    print(f"❌ Mahalle isteği başarısız. Kod: {response.status_code}")