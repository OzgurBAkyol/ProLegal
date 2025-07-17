import os

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from utils import plot_folium_polygon_map, save_csv

app = FastAPI(title="TKGM Parsel Sorgu API")


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


def append_props_to_csv(props: dict, filename: str = "parsel.csv"):
    return save_csv(props, filename)


def plot_parcel_on_map(coords, filename: str):
    if not coords or not coords[0]:
        return None
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    m = plot_folium_polygon_map(
        pd.DataFrame({"geometry": [coords]}), None, None, map_path=filename, zoom=16
    )
    return filename


@app.get("/parsel_sorgu")
def parsel_sorgu(mahalle_id: int, ada: int, parsel: int):
    data = get_parcel_json(mahalle_id, ada, parsel)
    coords, props = extract_parcel_info(data)
    csv_path = append_props_to_csv(props)
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


# uvicorn tkgm_api:app --reload --port 8000
