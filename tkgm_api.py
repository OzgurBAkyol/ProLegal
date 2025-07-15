import requests
from fastapi import HTTPException
import pandas as pd
import folium
import os

def get_parcel_json(mahalle_id: int, ada: int, parsel: int):
    url = f"https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/parsel/{mahalle_id}/{ada}/{parsel}"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Parsel bulunamadı veya API hatası.")
    return response.json()

def extract_parcel_info(data: dict):
    coords = data.get("geometry", {}).get("coordinates", [])
    props = data.get("properties", {})
    return coords, props

def append_props_to_csv(props: dict, filename: str = "parsel.csv"):
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
    folium.Polygon(locations=[(lat, lon) for lon, lat in coords[0]], color="red").add_to(m)
    m.save(filename)
    return filename 