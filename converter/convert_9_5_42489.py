# converter/convert_9_5_42489.py

import os
import csv
import re
from docx import Document

INPUT_FILE = "data/doc/9.5.42489.docx"
OUTPUT_FILE = "data/csv/9.5.42489.csv"

def convert_docx_to_csv(input_path, output_path):
    doc = Document(input_path)
    
    rows = []
    current_section = ""
    current_madde_no = ""
    current_title = ""
    current_content = ""

    def add_row():
        if current_madde_no:
            rows.append([current_section.strip(), current_madde_no.strip(), current_title.strip(), current_content.strip()])

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        if "BÖLÜM" in text:
            add_row()
            current_section = text
            current_madde_no = ""
            current_title = ""
            current_content = ""
            continue

        madde_match = re.match(r"^MADDE\s+(\d+)[-–]\s*(.*)", text)
        if madde_match:
            add_row()
            current_madde_no = madde_match.group(1)
            current_title = ""
            current_content = madde_match.group(2)
            continue

        if text.isupper():
            current_title = text
        else:
            current_content += " " + text

    add_row()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Bölüm", "Madde No", "Başlık", "İçerik"])
        writer.writerows(rows)

if __name__ == "__main__":
    convert_docx_to_csv(INPUT_FILE, OUTPUT_FILE)
    print(f"✅ CSV dosyası oluşturuldu: {OUTPUT_FILE}")