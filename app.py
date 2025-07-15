import streamlit as st
import requests
import pandas as pd
from streamlit_folium import st_folium
import folium
import os

st.set_page_config(page_title="ProLegal - Akıllı Mevzuat ve Parsel Asistanı", layout="wide")
st.title("ProLegal - Akıllı Mevzuat ve Parsel Asistanı")

st.sidebar.header("Menü")
menu = st.sidebar.radio("Seçim yapın", ["Mevzuat Asistanı", "Parsel Sorgu ve Harita"])

if menu == "Mevzuat Asistanı":
    st.header("Mevzuat Soru-Cevap (RAG Agent)")
    question = st.text_input("Soru sorun:")
    if st.button("Cevapla") and question:
        # Agent API'ye istek at (örnek: localde çalışan agent.py'nin bir endpointi olmalı)
        # Burada örnek olarak terminal agent.py yerine, bir API endpointi varsayalım:
        try:
            response = requests.post("http://localhost:8001/ask", json={"question": question})
            data = response.json()
            st.markdown(f"**Cevap:** {data.get('answer', 'Cevap alınamadı.')}")
            st.markdown(f"_Kullanılan veritabanları:_ {data.get('used_collections', '-')}")
        except Exception as e:
            st.error(f"Cevap alınamadı: {e}")

elif menu == "Parsel Sorgu ve Harita":
    st.header("Parsel Sorgula ve Haritada Göster")
    mahalle_id = st.number_input("Mahalle ID", min_value=1, value=150127)
    ada = st.number_input("Ada No", min_value=1, value=3718)
    parsel = st.number_input("Parsel No", min_value=1, value=1)
    if st.button("Parsel Sorgula"):
        with st.spinner("Sorgulanıyor..."):
            url = f"http://localhost:8000/parsel_sorgu?mahalle_id={mahalle_id}&ada={ada}&parsel={parsel}"
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                st.subheader("Parsel Özellikleri")
                st.json(data["ozellikler"])
                st.subheader("Koordinatlar")
                st.write(data["koordinatlar"])
                # Harita dosyasını oku ve göster
                map_path = data["harita_dosyasi"]
                if os.path.exists(map_path):
                    with open(map_path, "r") as f:
                        html = f.read()
                    st.components.v1.html(html, height=500)
                else:
                    # Alternatif: Koordinatları folium ile canlı çiz
                    coords = data["koordinatlar"]
                    if coords and coords[0]:
                        m = folium.Map(location=[coords[0][0][1], coords[0][0][0]], zoom_start=16)
                        folium.Polygon(locations=[(lat, lon) for lon, lat in coords[0]], color="red").add_to(m)
                        st_folium(m, width=700, height=500)
                # CSV dosyasını göster
                csv_path = data["csv_dosyasi"]
                if os.path.exists(csv_path):
                    st.subheader("CSV Kayıtları (Son eklenen dahil)")
                    df = pd.read_csv(csv_path)
                    st.dataframe(df.tail(10))
            else:
                st.error("API'den veri alınamadı.") 