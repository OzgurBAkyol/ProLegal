from fastapi import FastAPI, Query
from tkgm_api import get_parcel_json, extract_parcel_info, append_props_to_csv, plot_parcel_on_map
from typing import Any, Optional
import os

app = FastAPI()

@app.get("/parsel_sorgu")
def parsel_sorgu(
    mahalle_id: int = Query(..., description="Mahalle ID'si"),
    ada: int = Query(..., description="Ada numarası"),
    parsel: int = Query(..., description="Parsel numarası")
) -> Any:
    """
    TKGM API üzerinden parsel sorgulama yapar, sonucu parsel.csv'ye ekler ve harita görselini visual_map/ klasörüne kaydeder.
    """
    data = get_parcel_json(mahalle_id, ada, parsel)
    coords, props = extract_parcel_info(data)
    csv_path = append_props_to_csv(props, filename="parsel.csv")
    map_dir = "visual_map"
    map_path = os.path.join(map_dir, f"parsel_{mahalle_id}_{ada}_{parsel}.html")
    plot_parcel_on_map(coords, filename=map_path)
    result = {
        "mahalle_id": mahalle_id,
        "ada": ada,
        "parsel": parsel,
        "koordinatlar": coords,
        "ozellikler": props,
        "csv_dosyasi": csv_path,
        "harita_dosyasi": map_path
    }
    return result 