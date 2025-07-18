import json
import os
import sys
import uuid
from datetime import datetime
from io import BytesIO

import folium
import geopandas as gpd
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from shapely import geometry, wkt
from shapely.errors import WKTReadingError
from streamlit_folium import st_folium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

from mevzuat_rag.agent4 import chain, merged_retrieve

# --- Utils ve modüller ---
from utils import (
    apply_label,
    extract_osm_geometries,
    file_exists,
    filter_by_columns,
    fix_wkt,
    get_download_buffer,
    load_excel,
    load_polygons,
    load_slope_data,
    log_action,
    plot_folium_polygon_map,
    save_csv,
    save_excel,
    section_header,
    show_error,
    show_info,
    show_success,
    show_warning,
    to_excel_download_buffer,
)

# --- Ortak Ayarlar ---
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
}
CSV_PATH_IMAR = "data/imar_sonuclari.csv"
CSV_PATH_DETAY = "data/imar_detaylari.csv"
CSV_PATH_PARSEL = "data/parsel.csv"
KML_FOLDER = "kml_parseller"
DATA_DIR = "data"
VISUAL_MAP_DIR = "visual_map"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(KML_FOLDER, exist_ok=True)
os.makedirs(VISUAL_MAP_DIR, exist_ok=True)


def get_updated_parcel_from_browser(mahalle_id, ada, parsel):
    url = f"https://parselsorgu.tkgm.gov.tr/#/ara/idari/{mahalle_id}/{ada}/{parsel}/0"
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # GUI olmadan çalışsın
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        time.sleep(5)  # sayfanın yüklenmesini bekle
        try:
            show_link = driver.find_element(By.XPATH, '//*[@id="show-disabled-detail-link"]')
            show_link.click()
            time.sleep(2)
            yeni_adaparsel = driver.find_element(By.XPATH, '//*[@id="list-table"]/tbody/tr[2]/td[4]').text
            if "/" in yeni_adaparsel:
                yeni_ada, yeni_parsel = yeni_adaparsel.split("/")
                return int(yeni_ada), int(yeni_parsel)
        except Exception as e:
            return None, None
    finally:
        driver.quit()
    return None, None

def get_parcel_json(mahalle_id: int, ada: int, parsel: int, _rec=0, _info=None):
    url = f"https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/parsel/{mahalle_id}/{ada}/{parsel}"
    response = requests.get(url)
    if response.status_code != 200:
        return None, _info
    try:
        data = response.json()
        # Eğer geometry None ve gittigiParselListe varsa, yeni parsele yönlendir
        if (
            isinstance(data, dict)
            and (data.get("geometry") is None)
            and data.get("properties", {}).get("gittigiParselListe")
            and _rec < 2
        ):
            try:
                gitti = json.loads(data["properties"]["gittigiParselListe"])
                if (
                    gitti.get("features")
                    and len(gitti["features"]) > 0
                    and gitti["features"][0]["properties"].get("adaNo")
                    and gitti["features"][0]["properties"].get("parselNo")
                ):
                    yeni_ada = int(gitti["features"][0]["properties"]["adaNo"])
                    yeni_parsel = int(gitti["features"][0]["properties"]["parselNo"])
                    sebep = data["properties"].get("gittigiParselSebep", "Taşınmaz pasife alınmış.")
                    msg = f"Sorguladığınız parsel taşınmaz olarak pasife alınmış. {sebep} Yeni parsel: {yeni_ada}/{yeni_parsel}"
                    return get_parcel_json(mahalle_id, yeni_ada, yeni_parsel, _rec=_rec+1, _info=msg)
            except Exception:
                return None, _info
        return data, _info
    except Exception:
        return None, _info


def extract_parcel_info(data: dict):
    if not data or not isinstance(data, dict):
        return [], {}
    coords = data.get("geometry", {}).get("coordinates", [])
    props = data.get("properties", {})
    return coords, props


def append_props_to_csv(props: dict, filename: str):
    # Anahtar eşleştirme: API'den gelen property isimlerini tablo başlıklarına eşleştir
    mapping = {
        "mahalleAd": "Mahalle",
        "adaNo": "Ada",
        "parselNo": "Parsel",
        "alan": "Alan",
        "pafta": "Pafta"
    }
    props_clean = {k: (v if v is not None else "") for k, v in props.items()}
    # Eşleştirilmiş anahtarları ekle
    for src, dst in mapping.items():
        if src in props_clean:
            props_clean[dst] = props_clean[src]
    df_new = pd.DataFrame([props_clean])
    # Eğer dosya varsa, eksik sütunları tamamla ve sıralamayı koru
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        for col in df_new.columns:
            if col not in df.columns:
                df[col] = ""
        for col in df.columns:
            if col not in df_new.columns:
                df_new[col] = ""
        # Sütun sıralamasını koru
        df_new = df_new[df.columns]
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        # Eğer ilk kayıt ise, ana başlıkları öne al
        main_cols = ["Mahalle", "Ada", "Parsel", "Alan", "Pafta"]
        other_cols = [c for c in df_new.columns if c not in main_cols]
        df_new = df_new[main_cols + other_cols]
        df = df_new
    df = df.fillna("")
    df.to_csv(filename, index=False)
    return filename


def plot_parcel_on_map(coords, filename: str):
    if not coords or not coords[0]:
        return None
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    m = folium.Map(location=[coords[0][0][1], coords[0][0][0]], zoom_start=16)
    folium.Polygon(
        locations=[(lat, lon) for lon, lat in coords[0]], color="red"
    ).add_to(m)
    m.save(filename)
    return filename


def imar_sorgula(ada: int, parsel: int):
    sorgu_url = (
        f"https://eimar.dilovasi.bel.tr/imardurumu/service/imarsvc.aspx"
        f"?type=adaparsel&adaparsel={ada}/{parsel}&ilce=-100000&tmahalle=-100000&tamKelimeAra=1"
    )
    try:
        r1 = requests.get(sorgu_url, headers=HEADERS, timeout=10)
    except requests.exceptions.Timeout:
        st.error("Dilovası sunucusu yanıt vermedi (timeout).")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"İstek hatası: {e}")
        return None
    if r1.status_code != 200 or not r1.text.strip():
        st.error("Sorgu başarısız")
        return None
    try:
        json_data = r1.json()
        objectid = json_data[0]["OBJECTID"]
        mahalle = json_data[0].get("TAPU_MAH_ADI", "Bilinmiyor")
    except Exception as e:
        st.error(f"JSON parse hatası: {e}")
        return None
    imar_url = f"https://eimar.dilovasi.bel.tr/imardurumu/imar.aspx?parselid={objectid}"
    try:
        r2 = requests.get(imar_url, headers=HEADERS, timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"İmar sayfası alınamadı: {e}")
        return None
    soup = BeautifulSoup(r2.text, "html.parser")
    save_csv(
        {"Mahalle": mahalle, "Ada": ada, "Parsel": parsel, "OBJECTID": objectid},
        CSV_PATH_IMAR,
    )
    detay = {"Mahalle": mahalle, "Ada": ada, "Parsel": parsel, "OBJECTID": objectid}
    for table_row in soup.select("div.divTableRow"):
        label = table_row.select_one("div.divTableCellLabel")
        value = table_row.select_one("div.divTableContent")
        if label and value:
            key = label.get_text(strip=True)
            val = value.get_text(strip=True)
            if key:
                detay[key] = val
    fonksiyonlar = [a.get_text(strip=True) for a in soup.select("a.fonksiyonalani")]
    if fonksiyonlar:
        detay["Plan Fonksiyonu"] = " | ".join(fonksiyonlar)
    save_csv(detay, CSV_PATH_DETAY)
    # KML dosyası
    kml_url = (
        f"https://eimar.dilovasi.bel.tr/imardurumu/service/kml.ashx?token={objectid}"
    )
    kml_path = os.path.join(KML_FOLDER, f"parsel_{ada}{parsel}{objectid}.kml")
    try:
        r_kml = requests.get(kml_url, headers=HEADERS, timeout=30)
        if r_kml.status_code == 200:
            with open(kml_path, "wb") as f:
                f.write(r_kml.content)
        else:
            kml_path = f"KML indirilemedi: {r_kml.status_code}"
    except Exception as e:
        kml_path = f"KML hata: {e}"
    return {
        "success": True,
        "objectid": objectid,
        "used_mahalle": mahalle,
        "source_url": imar_url,
        "kml_file": kml_path,
        "csv_kayit": CSV_PATH_DETAY,
    }


# --- Mevzuat RAG UI ---
def mevzuat_rag_ui():
    section_header(
        "Mevzuat Soru-Cevap (RAG Agent)",
        description="Mevzuat dosyalarından embedding ile bilgi çekip, OpenRouter LLM ile Türkçe cevap alabilirsiniz.",
        help_text="Soru sorduğunuzda, ilgili mevzuat koleksiyonlarından veri çekilir ve hangi koleksiyonlardan faydalanıldığı belirtilir.",
    )
    question = st.text_input("Soru sorun:")
    if st.button("Cevapla") and question:
        with st.spinner("Cevap oluşturuluyor..."):
            reviews, used_collections = merged_retrieve(question)
            result = chain.invoke({"reviews": reviews, "question": question})
            if used_collections:
                result += (
                    "\n\n---\nBu cevabın oluşturulmasında kullanılan veritabanları: "
                    + ", ".join(used_collections)
                )
            else:
                result += "\n\n---\nBu cevabın oluşturulmasında hiçbir veritabanı kullanılmadı."
            st.markdown(result)


# --- Parsel Sorgu ve Harita UI ---
def parsel_sorgu_ui():
    section_header(
        "Parsel Sorgula ve Haritada Göster",
        description="TKGM API ile parsel sorgulama ve harita üzerinde görselleştirme.",
        help_text="Mahalle, ada ve parsel numarası girerek sorgulama yapabilirsiniz. Sonuçlar CSV'ye kaydedilir ve harita olarak görüntülenir.",
    )
    mahalle_id = st.number_input("Mahalle ID", min_value=1, value=150127)
    ada = st.number_input("Ada No", min_value=1, value=3718)
    parsel = st.number_input("Parsel No", min_value=1, value=1)
    if st.button("Parsel Sorgula"):
        data, info_msg = get_parcel_json(mahalle_id, ada, parsel)
        if info_msg:
            st.info(info_msg)
        if data and isinstance(data, dict):
            coords, props = extract_parcel_info(data)
            if coords and props:
                csv_path = append_props_to_csv(props, filename=CSV_PATH_PARSEL)
                map_path = f"{VISUAL_MAP_DIR}/parsel_{mahalle_id}{ada}{parsel}.html"
                harita_dosyasi = plot_parcel_on_map(coords, map_path)
                st.subheader("Parsel Özellikleri")
                st.json(props)
                st.markdown("Koordinatlar: [...]")
                with st.expander("Detaylı Koordinatları Göster"):
                    st.write(coords)
                if harita_dosyasi and os.path.exists(harita_dosyasi):
                    with open(harita_dosyasi, "r") as f:
                        html = f.read()
                    st.components.v1.html(html, height=500)
                elif coords and coords[0]:
                    m = folium.Map(location=[coords[0][0][1], coords[0][0][0]], zoom_start=16)
                    folium.Polygon(locations=[(lat, lon) for lon, lat in coords[0]], color="red").add_to(m)
                    st_folium(m, width=700, height=500)
                if csv_path and os.path.exists(csv_path):
                    st.subheader("CSV Kayıtları (Son eklenen dahil)")
                    df = pd.read_csv(csv_path)
                    st.dataframe(df.tail(10))
            # else: hiçbir açıklama veya hata mesajı gösterme
        else:
            show_error("Parsel verisi alınamadı.")


# --- İmar Sorgu UI ---
def imar_sorgu_ui():
    section_header(
        "İmar Sorgu",
        description="Dilovası Belediyesi imar sorgu ve KML/KMZ dosya işlemleri.",
        help_text="Ada ve parsel girerek imar detaylarını, KML/KMZ dosyasını ve CSV kaydını görebilirsiniz.",
    )
    ada = st.number_input("Ada", min_value=0, value=1, key="imar_ada")
    parsel = st.number_input("Parsel", min_value=0, value=1, key="imar_parsel")
    if st.button("İmar Sorgula"):
        import traceback

        with st.spinner("Sorgulanıyor, lütfen bekleyin..."):
            try:
                data = imar_sorgula(ada, parsel)
                st.session_state["imar_sonuc"] = data
                st.session_state["imar_hata"] = None
            except Exception as e:
                st.session_state["imar_sonuc"] = None
                st.session_state["imar_hata"] = f"Hata: {e}\n{traceback.format_exc()}"
    if st.session_state.get("imar_hata"):
        show_error(st.session_state["imar_hata"])
    elif st.session_state.get("imar_sonuc"):
        data = st.session_state["imar_sonuc"]
        st.json(data)
        kml_path = data.get("kml_file")
        if kml_path and os.path.exists(kml_path):
            # KML/KMZ dosya işlemleri ve harita gösterimi burada olacak (kodu utils'e taşı)
            pass  # ...
        else:
            show_warning("KML dosyası bulunamadı veya indirilemedi.")
        csv_path = data.get("csv_kayit")
        if csv_path and os.path.exists(csv_path):
            st.subheader("İmar Detayları Tablosu")
            try:
                df = pd.read_csv(csv_path)
                st.dataframe(df.tail(10))
            except Exception as e:
                show_error(f"CSV dosyası okunamadı: {e}")


# --- Poligon Analiz UI ---
def poligon_analiz_ui():
    section_header(
        "Poligon Analizi: Yapı, Yol ve Eğim (Google API + OSM)",
        description="Poligonların yapılaşma, yol yakınlığı ve eğim analizini yapabilirsiniz.",
        help_text="Poligon, eğim ve OSM verileriyle analiz ve harita görselleştirme.",
    )
    gdf = load_polygons("data/poligon.json").to_crs("EPSG:4326")
    slope_df = load_slope_data("data/slope/slope_cache.csv")
    buildings, roads = extract_osm_geometries("data/osm_results")
    gdf = gdf.merge(slope_df, on="ID", how="left")
    gdf["Yapı Var"] = gdf.geometry.apply(
        lambda p: not buildings[buildings.intersects(p)].empty
    )
    gdf["Yol Var"] = gdf.geometry.apply(lambda p: not roads[roads.intersects(p)].empty)
    st.sidebar.header("🔍 Filtrele")
    if st.sidebar.checkbox("🏠 Yapı İçeren"):
        gdf = gdf[gdf["Yapı Var"]]
    if st.sidebar.checkbox("🌾 Yol İçeren"):
        gdf = gdf[gdf["Yol Var"]]
    if st.sidebar.checkbox("⛔ Yol ve Yapı İçermeyen"):
        gdf = gdf[~gdf["Yapı Var"] & ~gdf["Yol Var"]]
    if st.sidebar.checkbox("🌄 %10+ Eğim Sahip"):
        gdf = gdf[gdf["Eğim (%)"] >= 10]
    st.subheader(f"📊 Eşleşen Poligon Sayısı: {len(gdf)}")
    st.dataframe(
        gdf[["ID", "Yapı Var", "Yol Var", "Eğim (%)"]], use_container_width=True
    )
    if not gdf.empty:
        m = plot_folium_polygon_map(gdf, buildings, roads)
        st_folium(m, height=700, width=1200)
    else:
        show_warning("Gösterilecek poligon bulunamadı.")


# --- Parsel Etiketleme UI ---
def parsel_etiketleme_ui():
    section_header(
        "Dilovası Parsel Filtreleme & Etiketleme Aracı",
        description="5 sütunlu veri üzerinde 3 sütuna göre filtreleme ve satırlara etiket atama.",
        help_text="Filtreleme, etiketleme, loglama ve Excel'e indirme işlemleri.",
    )
    FILE_PATH = "data/csv/dilovası.xlsx"
    LOG_PATH = "data/logs/etiket_log.csv"
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
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


# --- GÖRSEL VE YAZISAL İYİLEŞTİRMELER ---
# Sayfa ayarları ve logo (varsa)
st.set_page_config(page_title="ProLegal - Akıllı Mevzuat ve Parsel Asistanı", page_icon="⚖️", layout="wide")
try:
    st.image("logo.png", width=120)
except Exception:
    pass
st.title("ProLegal - Akıllı Mevzuat ve Parsel Asistanı")
st.markdown("#### 👋 Hoşgeldiniz! Aşağıdaki menüden istediğiniz modülü seçebilirsiniz.")

# --- Streamlit Menü ve Arayüz ---
st.sidebar.header("Menü")
menu = st.sidebar.radio(
    "Seçim yapın",
    [
        "Mevzuat Asistanı",
        "Parsel Sorgu ve Harita",
        "İmar Sorgu",
        "Poligon Analizi",
        "Parsel Etiketleme"
    ]
)

if menu == "Mevzuat Asistanı":
    st.header("📚 Mevzuat Soru-Cevap (RAG Agent)")
    st.markdown("Yapay zeka destekli mevzuat asistanı ile Türkçe mevzuat sorularınızı yanıtlayabilirsiniz.")
    with st.expander("🔎 Nasıl Çalışır?"):
        st.write("Mevzuat dosyalarından embedding ile bilgi çekilir, OpenRouter LLM ile Türkçe cevap oluşturulur. Soru, vektör arama ile ilgili mevzuat parçalarıyla eşleştirilir ve modelden yanıt alınır.")
    mevzuat_rag_ui()
elif menu == "Parsel Sorgu ve Harita":
    st.header("🗺️ Parsel Sorgula ve Haritada Göster")
    st.markdown("TKGM üzerinden parsel sorgulaması yapabilir ve sonucu haritada görebilirsiniz.")
    with st.expander("🔎 Nasıl Çalışır?"):
        st.write("Girilen mahalle, ada ve parsel bilgisiyle TKGM API'sine sorgu atılır, dönen geometri haritada gösterilir ve özellikler tabloya kaydedilir.")

    # Mahalle ID seçim kutusu (yeni özellik)
    mahalle_df = None
    try:
        mahalle_df = pd.read_csv("data/mahalle_id.csv")
    except Exception:
        st.warning("Mahalle ID listesi yüklenemedi, manuel giriş yapabilirsiniz.")
    mahalle_id = None
    if mahalle_df is not None and "MahalleID" in mahalle_df.columns and "MahalleAdı" in mahalle_df.columns:
        mahalle_options = [f"{row.MahalleID} ({row.MahalleAdı})" for _, row in mahalle_df.iterrows()]
        mahalle_map = {f"{row.MahalleID} ({row.MahalleAdı})": row.MahalleID for _, row in mahalle_df.iterrows()}
        secim = st.selectbox("Mahalle ID seçin", mahalle_options)
        mahalle_id = mahalle_map[secim]
    else:
        mahalle_id = st.number_input("Mahalle ID", min_value=1, value=150127)

    ada = st.number_input("Ada No", min_value=0, value=3718)
    parsel = st.number_input("Parsel No", min_value=0, value=1)
    if st.button("Parsel Sorgula"):
        data, info_msg = get_parcel_json(mahalle_id, ada, parsel)
        if info_msg:
            st.info(info_msg)
        if data and isinstance(data, dict):
            coords, props = extract_parcel_info(data)
            if coords and props:
                csv_path = append_props_to_csv(props, filename=CSV_PATH_PARSEL)
                map_path = f"visual_map/parsel_{mahalle_id}{ada}{parsel}.html"
                harita_dosyasi = plot_parcel_on_map(coords, map_path)
                st.subheader("Parsel Özellikleri")
                st.json(props)
                st.markdown("Koordinatlar: [...]")
                with st.expander("Detaylı Koordinatları Göster"):
                    st.write(coords)
                if harita_dosyasi and os.path.exists(harita_dosyasi):
                    with open(harita_dosyasi, "r") as f:
                        html = f.read()
                    st.components.v1.html(html, height=500)
                elif coords and coords[0]:
                    m = folium.Map(location=[coords[0][0][1], coords[0][0][0]], zoom_start=16)
                    folium.Polygon(locations=[(lat, lon) for lon, lat in coords[0]], color="red").add_to(m)
                    st_folium(m, width=700, height=500)
                if csv_path and os.path.exists(csv_path):
                    st.subheader("CSV Kayıtları (Son eklenen dahil)")
                    df = pd.read_csv(csv_path)
                    st.dataframe(df.tail(10))
            # else: hiçbir açıklama veya hata mesajı gösterme
        else:
            st.error("Parsel verisi alınamadı.")
elif menu == "İmar Sorgu":
    st.header("🏢 İmar Sorgu")
    st.markdown("Dilovası Belediyesi imar sorgulama servisi ile ada/parsel bazında imar durumu sorgulayabilirsiniz.")
    with st.expander("🔎 Nasıl Çalışır?"):
        st.write("Ada ve parsel ile belediye API'sine sorgu atılır, dönen imar bilgileri ve KML dosyası harita ve tablo olarak sunulur.")
    imar_sorgu_ui()
elif menu == "Poligon Analizi":
    st.header("🏡 Poligon Analizi: Yapı, Yol ve Eğim (Google API + OSM)")
    st.markdown("Poligonların yapılaşma, yol yakınlığı ve eğim analizini harita üzerinde inceleyebilirsiniz.")
    with st.expander("🔎 Nasıl Çalışır?"):
        st.write("Poligonların centroid noktası üzerinden eğim (slope) verisi alınır, OSM'den yol ve yapı geometrileri çekilir, tüm analizler harita ve tabloya yansıtılır.")
    poligon_analiz_ui()
elif menu == "Parsel Etiketleme":
    st.header("🏷️ Dilovası Parsel Filtreleme & Etiketleme Aracı")
    st.markdown("5 sütunlu veri üzerinde 3 sütuna göre filtreleme ve satırlara etiket atama işlemlerini kolayca yapabilirsiniz.")
    with st.expander("🔎 Nasıl Çalışır?"):
        st.write("Excel dosyasındaki parseller filtrelenir, seçilen satırlara etiket atanır ve sonuçlar kaydedilip indirilebilir.")
    parsel_etiketleme_ui()