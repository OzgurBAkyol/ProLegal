import json
import os

import folium
import geopandas as gpd
import pandas as pd
from shapely import geometry, wkt
from shapely.errors import WKTReadingError


def fix_wkt(wkt_str):
    try:
        return wkt.loads(wkt_str)
    except WKTReadingError:
        try:
            while wkt_str.startswith("("):
                wkt_str = wkt_str[1:-1]
            return wkt.loads(wkt_str)
        except:
            return None


def load_polygons(path: str, crs="EPSG:3857"):
    with open(path) as f:
        raw = json.load(f)
    df = pd.DataFrame(raw)
    df["geometry"] = df["geometry"].apply(lambda x: fix_wkt(x) if x else None)
    df = df[df["geometry"].notnull()]
    df["ID"] = df["ID"].astype(str)
    return gpd.GeoDataFrame(df, geometry="geometry", crs=crs)


def load_slope_data(path: str):
    slope_df = pd.read_csv(path)
    slope_df["ID"] = slope_df["ID"].astype(str)
    if "Eğim (°)" in slope_df.columns:
        slope_df.rename(columns={"Eğim (°)": "Eğim (%)"}, inplace=True)
    return slope_df


def extract_osm_geometries(folder_path):
    roads, buildings = [], []
    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            with open(os.path.join(folder_path, file)) as f:
                data = json.load(f)
            nodes = {
                el["id"]: (el["lon"], el["lat"])
                for el in data.get("elements", [])
                if el["type"] == "node"
            }
            for el in data.get("elements", []):
                if el["type"] == "way" and "nodes" in el:
                    coords = [nodes[n] for n in el["nodes"] if n in nodes]
                    if len(coords) < 2:
                        continue
                    if coords[0] == coords[-1] and len(coords) >= 4:
                        geom = geometry.Polygon(coords)
                    else:
                        geom = geometry.LineString(coords)
                    if "building" in el.get("tags", {}) and isinstance(
                        geom, geometry.Polygon
                    ):
                        buildings.append(geom)
                    elif "highway" in el.get("tags", {}) and isinstance(
                        geom, geometry.LineString
                    ):
                        roads.append(geom)
    gdf_buildings = gpd.GeoDataFrame(geometry=buildings, crs="EPSG:4326")
    gdf_roads = gpd.GeoDataFrame(geometry=roads, crs="EPSG:4326")
    return gdf_buildings, gdf_roads


def plot_folium_polygon_map(gdf, buildings, roads, map_path=None, zoom=12):
    if gdf.empty:
        return None
    buildings4326 = buildings.to_crs("EPSG:4326")
    roads4326 = roads.to_crs("EPSG:4326")
    m = folium.Map(
        location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()],
        zoom_start=zoom,
        tiles="OpenStreetMap",
    )
    for _, row in gdf.iterrows():
        tooltip = f"Eğim: %{row.get('Eğim (%)','')}, Yapı: {row.get('Yapı Var','')}, Yol: {row.get('Yol Var','')}"
        folium.GeoJson(
            row.geometry,
            tooltip=tooltip,
            style_function=lambda x: {
                "fillColor": "orange",
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.5,
            },
        ).add_to(m)
    for _, row in buildings4326.iterrows():
        folium.GeoJson(
            row.geometry,
            style_function=lambda x: {
                "fillColor": "red",
                "color": "red",
                "weight": 0.5,
                "fillOpacity": 0.5,
            },
        ).add_to(m)
    for _, row in roads4326.iterrows():
        folium.GeoJson(
            row.geometry,
            style_function=lambda x: {"color": "blue", "weight": 1.2, "opacity": 0.6},
        ).add_to(m)
    if map_path:
        m.save(map_path)
    return m
