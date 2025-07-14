import os
import csv
import re
import docx2txt

INPUT_FILE = "data/doc/9.5.42456.docx"
OUTPUT_FILE = "data/csv/9.5.42456.csv"

def extract_text_from_docx(docx_path):
    return docx2txt.process(docx_path)

def parse_text_to_rows(text):
    lines = text.splitlines()
    rows = []

    current_madde = ""
    current_baslik = ""
    current_icerik = ""

    def add_row():
        if current_madde and current_icerik.strip():
            rows.append([
                current_madde.strip(),
                current_baslik.strip(),
                current_icerik.strip()
            ])

    for line in lines:
        line = line.strip()
        if not line:
            continue

        madde_match = re.match(r"^(GEÇİCİ\s+)?MADDE\s+(\d+)[-–]?\s*(.*)", line)
        if madde_match:
            add_row()
            gecici = madde_match.group(1) or ""
            madde_no = madde_match.group(2)
            current_madde = f"{gecici}{madde_no}".strip()
            current_icerik = madde_match.group(3).strip()
            current_baslik = ""
            continue

        if line.isupper() and len(line.split()) <= 5:
            current_baslik = line.strip()
        else:
            current_icerik += " " + line.strip()

    add_row()
    return rows

def save_rows_to_csv(rows, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Madde No", "Başlık", "İçerik"])
        writer.writerows(rows)

if __name__ == "__main__":
    print(f"📄 Belge okunuyor: {INPUT_FILE}")
    full_text = extract_text_from_docx(INPUT_FILE)
    rows = parse_text_to_rows(full_text)
    save_rows_to_csv(rows, OUTPUT_FILE)
    print(f"✅ CSV dosyası oluşturuldu: {OUTPUT_FILE}")