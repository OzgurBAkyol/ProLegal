import streamlit as st
from streamlit_folium import st_folium

from utils import (
    extract_osm_geometries,
    load_polygons,
    load_slope_data,
    plot_folium_polygon_map,
    section_header,
    show_warning,
)


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


if __name__ == "__main__":
    poligon_analiz_ui()
