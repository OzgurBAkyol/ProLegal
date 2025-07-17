import os

import streamlit as st

from utils import (
    apply_label,
    get_download_buffer,
    load_excel,
    section_header,
    show_success,
)

FILE_PATH = "data/csv/dilovası.xlsx"
LOG_PATH = "data/logs/etiket_log.csv"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def parsel_etiketleme_ui():
    section_header(
        "Dilovası Parsel Filtreleme & Etiketleme Aracı",
        description="5 sütunlu veri üzerinde 3 sütuna göre filtreleme ve satırlara etiket atama.",
        help_text="Filtreleme, etiketleme, loglama ve Excel'e indirme işlemleri.",
    )
    df = load_excel(FILE_PATH)
    if "Etiket" not in df.columns:
        df["Etiket"] = ""
    st.sidebar.header("🔍 Filtre Seç")
    il = st.sidebar.selectbox("İl", sorted(df["İl"].dropna().unique()))
    ilce = st.sidebar.selectbox(
        "İlçe", sorted(df[df["İl"] == il]["İlçe"].dropna().unique())
    )
    mahalle = st.sidebar.selectbox(
        "Mahalle",
        sorted(
            df[(df["İl"] == il) & (df["İlçe"] == ilce)]["Mahalle"].dropna().unique()
        ),
    )
    etiket_filtre = st.sidebar.selectbox(
        "Etiket Filtrele", ["Tümü", "Uygun", "Red", "Beklemede"]
    )
    filtered_df = df[
        (df["İl"] == il) & (df["İlçe"] == ilce) & (df["Mahalle"] == mahalle)
    ]
    if etiket_filtre != "Tümü":
        filtered_df = filtered_df[filtered_df["Etiket"] == etiket_filtre]
    st.subheader(f"📊 Eşleşen Parseller: {len(filtered_df)} adet")
    filtered_df["Seç"] = False
    selected = st.data_editor(
        filtered_df,
        column_order=["Seç"] + [col for col in filtered_df.columns if col != "Seç"],
        num_rows="dynamic",
        use_container_width=True,
        key="editor",
    )
    secili_satirlar = selected[selected["Seç"]]
    if not secili_satirlar.empty:
        st.markdown("### 🎯 Seçilen Parsellere Etiket Ata")
        yeni_etiket = st.selectbox("Etiket Seç", ["Uygun", "Red", "Beklemede"])
        if st.button("✅ Etiketi Uygula"):
            df = apply_label(
                df, secili_satirlar.index, yeni_etiket, FILE_PATH, LOG_PATH
            )
            show_success("Seçilenlere etiket uygulandı ve loglandı.")
    st.markdown("---")
    buffer = get_download_buffer(df)
    st.download_button(
        label="📥 Etiketlenmiş Veriyi İndir (Excel)",
        data=buffer,
        file_name="etiketlenmis_veri.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    parsel_etiketleme_ui()
