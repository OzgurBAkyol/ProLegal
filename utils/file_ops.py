import json
import os
from datetime import datetime
from io import BytesIO

import pandas as pd


def save_csv(data: dict, path: str):
    df_new = pd.DataFrame([data])
    if os.path.exists(path):
        df = pd.read_csv(path)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(path, index=False)
    return path


def save_excel(df: pd.DataFrame, path: str):
    df.to_excel(path, index=False)
    return path


def load_excel(path: str):
    return pd.read_excel(path, engine="openpyxl")


def save_json(data: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def log_action(log_path: str, log_data: dict):
    df_new = pd.DataFrame([log_data])
    if os.path.exists(log_path):
        df = pd.read_csv(log_path)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(log_path, index=False)
    return log_path


def to_excel_download_buffer(df: pd.DataFrame):
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer


def file_exists(path: str):
    return os.path.exists(path)
