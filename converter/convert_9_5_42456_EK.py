# converter/convert_9_5_42456_EK.py

import os
import csv
from docx import Document

INPUT_FILE = "data/doc/9.5.42456 EK.docx"
OUTPUT_FILE = "data/csv/9.5.42456_EK.csv"

def convert_ek_blocks_to_csv(input_path, output_path):
    doc = Document(input_path)

    rows = []
    current_ek = ""
    current_title = ""
    current_content = ""

    def flush():
        if current_ek and current_title and current_content.strip():
            rows.append([current_ek, current_title.strip(), current_content.strip()])

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        if text.startswith("EK-"):
            flush()
            parts = text.split(None, 1)
            current_ek = parts[0].strip()
            current_title = parts[1].strip() if len(parts) > 1 else ""
            current_content = ""
        elif current_ek and not current_title:
            # Başlığı ayrı satırda yazmış olabilir
            current_title = text
        else:
            current_content += text + " "

    flush()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["EK", "Başlık", "İçerik"])
        writer.writerows(rows)

    print(f"✅ CSV oluşturuldu: {output_path}")
    print(f"➡️ Toplam satır sayısı: {len(rows)}")

if __name__ == "__main__":
    convert_ek_blocks_to_csv(INPUT_FILE, OUTPUT_FILE)