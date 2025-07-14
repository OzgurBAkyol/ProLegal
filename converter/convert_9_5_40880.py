# converter/convert_9_5_40880.py

import os
import csv
import re
from docx import Document

INPUT_FILE = "data/doc/9.5.40880.docx"
OUTPUT_FILE = "data/csv/9.5.40880.csv"

def convert_docx_to_csv(input_path, output_path):
    doc = Document(input_path)

    rows = []
    current_madde = ""
    current_baslik = ""
    current_icerik = ""

    def add_row():
        if current_madde:
            rows.append([current_madde.strip(), current_baslik.strip(), current_icerik.strip()])

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        madde_match = re.match(r"^(GEÇİCİ\s+)?MADDE\s+(\d+)[-–]?\s*(.*)", text, re.IGNORECASE)
        if madde_match:
            add_row()
            gecici = madde_match.group(1) or ""
            current_madde = f"{gecici.strip()} {madde_match.group(2)}".strip()
            current_icerik = madde_match.group(3)
            continue

        if text.isupper():
            current_baslik = text
        else:
            current_icerik += " " + text

    add_row()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Madde No", "Başlık", "İçerik"])
        writer.writerows(rows)

if __name__ == "__main__":
    convert_docx_to_csv(INPUT_FILE, OUTPUT_FILE)
    print(f"✅ CSV dosyası oluşturuldu: {OUTPUT_FILE}")