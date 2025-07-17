import os

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query

from utils import save_csv

app = FastAPI(title="Dilovası İmar Sorgu API")

CSV_PATH = "imar_sonuclari.csv"


def yaz_csv(dikt: dict):
    save_csv(dikt, CSV_PATH)


@app.get("/sorgula")
def sorgula(
    ada: int = Query(...), parsel: int = Query(...), mahalle: str = Query(None)
):
    sorgu_url = f"https://eimar.dilovasi.bel.tr/imardurumu/imarsvc.aspx?type=adaparsel&adaparsel={ada}/{parsel}"
    r1 = requests.get(sorgu_url)
    if r1.status_code != 200 or not r1.text.strip():
        return {
            "success": False,
            "message": "Sorgu başarısız veya veri yok",
            "url": sorgu_url,
        }
    try:
        data = r1.json()[0]
        objectid = data["OBJECTID"]
        mahalle_from_json = data.get("TAPU_MAH_ADI", "Bilinmiyor")
        mahalle = mahalle or mahalle_from_json
    except Exception as e:
        return {
            "success": False,
            "message": f"ObjectID veya mahalle alınamadı: {e}",
            "raw_response": r1.text,
        }
    imar_url = f"https://eimar.dilovasi.bel.tr/imardurumu/imar.aspx?parselid={objectid}"
    r2 = requests.get(imar_url)
    soup = BeautifulSoup(r2.text, "html.parser")
    sonuc = {"Mahalle": mahalle, "Ada": ada, "Parsel": parsel}
    for tablo in soup.find_all("table"):
        for row in tablo.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                val = cols[1].get_text(strip=True)
                if key:
                    sonuc[key] = val
    for th in soup.find_all("th"):
        key = th.get_text(strip=True)
        td = th.find_next_sibling("td")
        if td:
            sonuc[key] = td.get_text(strip=True)
    save_csv(sonuc, CSV_PATH)
    return {
        "success": True,
        "data": sonuc,
        "used_mahalle": mahalle,
        "objectid": objectid,
        "source_url": imar_url,
    }
