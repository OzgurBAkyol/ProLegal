import csv
import os

import folium
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="ProLegal İmar & Parsel Sorgu API")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
}

CSV_PATH_IMAR = "data/imar_sonuclari.csv"
CSV_PATH_DETAY = "data/imar_detaylari.csv"
CSV_PATH_PARSEL = "data/parsel.csv"
KML_FOLDER = "kml_parseller"

os.makedirs("data", exist_ok=True)
os.makedirs(KML_FOLDER, exist_ok=True)
os.makedirs("visual_map", exist_ok=True)


def yaz_csv(dikt: dict, path: str):
    df_new = pd.DataFrame([dikt])
    if os.path.exists(path):
        df = pd.read_csv(path)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(path, index=False)


@app.get("/imar_sorgula")
def imar_sorgula(ada: int = Query(...), parsel: int = Query(...)):
    sorgu_url = (
        f"https://eimar.dilovasi.bel.tr/imardurumu/service/imarsvc.aspx"
        f"?type=adaparsel&adaparsel={ada}/{parsel}&ilce=-100000&tmahalle=-100000&tamKelimeAra=1"
    )

    try:
        r1 = requests.get(sorgu_url, headers=HEADERS, timeout=10)
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail="Dilovası sunucusu yanıt vermedi (timeout)."
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"İstek hatası: {e}")

    if r1.status_code != 200 or not r1.text.strip():
        return {"success": False, "message": "Sorgu başarısız", "url": sorgu_url}

    try:
        json_data = r1.json()
        objectid = json_data[0]["OBJECTID"]
        mahalle = json_data[0].get("TAPU_MAH_ADI", "Bilinmiyor")
    except Exception as e:
        return {
            "success": False,
            "message": f"JSON parse hatası: {e}",
            "raw_response": r1.text,
        }

    imar_url = f"https://eimar.dilovasi.bel.tr/imardurumu/imar.aspx?parselid={objectid}"

    try:
        r2 = requests.get(imar_url, headers=HEADERS, timeout=10)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"İmar sayfası alınamadı: {e}")

    soup = BeautifulSoup(r2.text, "html.parser")

    yaz_csv(
        {"Mahalle": mahalle, "Ada": ada, "Parsel": parsel, "OBJECTID": objectid},
        CSV_PATH_IMAR,
    )

    detay = {"Mahalle": mahalle, "Ada": ada, "Parsel": parsel, "OBJECTID": objectid}

    for table_row in soup.select("div.divTableRow"):
        label = table_row.select_one("div.divTableCellLabel")
        value = table_row.select_one("div.divTableContent")
        if label and value:
            key = label.get_text(strip=True)
            val = value.get_text(strip=True)
            if key:
                detay[key] = val

    fonksiyonlar = [a.get_text(strip=True) for a in soup.select("a.fonksiyonalani")]
    if fonksiyonlar:
        detay["Plan Fonksiyonu"] = " | ".join(fonksiyonlar)

    yaz_csv(detay, CSV_PATH_DETAY)

    # KML dosyası
    kml_url = (
        f"https://eimar.dilovasi.bel.tr/imardurumu/service/kml.ashx?token={objectid}"
    )
    kml_path = os.path.join(KML_FOLDER, f"parsel_{ada}_{parsel}_{objectid}.kml")
    try:
        r_kml = requests.get(kml_url, headers=HEADERS, timeout=10)
        if r_kml.status_code == 200:
            with open(kml_path, "wb") as f:
                f.write(r_kml.content)
        else:
            kml_path = f"KML indirilemedi: {r_kml.status_code}"
    except Exception as e:
        kml_path = f"KML hata: {e}"

    return JSONResponse(
        {
            "success": True,
            "objectid": objectid,
            "used_mahalle": mahalle,
            "source_url": imar_url,
            "kml_file": kml_path,
            "csv_kayit": CSV_PATH_DETAY,
        }
    )


# ─────────────────────────────
# TKGM PARSEL SORGUSU
# ─────────────────────────────


def get_parcel_json(mahalle_id: int, ada: int, parsel: int):
    url = f"https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/parsel/{mahalle_id}/{ada}/{parsel}"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(
            status_code=404, detail="Parsel bulunamadı veya API hatası."
        )
    return response.json()


def extract_parcel_info(data: dict):
    coords = data.get("geometry", {}).get("coordinates", [])
    props = data.get("properties", {})
    return coords, props


def append_props_to_csv(props: dict, filename: str):
    df_new = pd.DataFrame([props])
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(filename, index=False)
    return filename


def plot_parcel_on_map(coords, filename: str):
    if not coords or not coords[0]:
        return None
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    m = folium.Map(location=[coords[0][0][1], coords[0][0][0]], zoom_start=16)
    folium.Polygon(
        locations=[(lat, lon) for lon, lat in coords[0]], color="red"
    ).add_to(m)
    m.save(filename)
    return filename


@app.get("/parsel_sorgula")
def parsel_sorgula(mahalle_id: int, ada: int, parsel: int):
    data = get_parcel_json(mahalle_id, ada, parsel)
    coords, props = extract_parcel_info(data)
    csv_path = append_props_to_csv(props, CSV_PATH_PARSEL)
    map_path = f"visual_map/parsel_{mahalle_id}_{ada}_{parsel}.html"
    harita_dosyasi = plot_parcel_on_map(coords, map_path)
    return JSONResponse(
        {
            "ozellikler": props,
            "koordinatlar": coords,
            "csv_dosyasi": csv_path,
            "harita_dosyasi": harita_dosyasi,
        }
    )


# uvicorn api_main:app --reload
