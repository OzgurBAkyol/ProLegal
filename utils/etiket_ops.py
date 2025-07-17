import os
from datetime import datetime

import pandas as pd

from utils.file_ops import load_excel, log_action, save_excel, to_excel_download_buffer


def filter_by_columns(df, filters: dict):
    for col, val in filters.items():
        if val is not None:
            df = df[df[col] == val]
    return df


def apply_label(df, indices, label, file_path, log_path):
    df.loc[indices, "Etiket"] = label
    save_excel(df, file_path)
    log_entries = []
    for idx in indices:
        row = df.loc[idx]
        log_entries.append(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "il": row.get("İl", ""),
                "ilce": row.get("İlçe", ""),
                "mahalle": row.get("Mahalle", ""),
                "parsel": row.get("Parsel", ""),
                "etiket": label,
            }
        )
    for entry in log_entries:
        log_action(log_path, entry)
    return df


def get_download_buffer(df):
    return to_excel_download_buffer(df)
