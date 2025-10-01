import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🚗 Rutas más cortas entre orígenes y destinos (OSRM)")

# Subida de ficheros
origenes_file = st.file_uploader("📍 Sube CSV de orígenes", type="csv")
destinos_file = st.file_uploader("🏁 Sube CSV de destinos", type="csv")

OSRM_URL = "http://router.project-osrm.org/route/v1/driving"

if origenes_file and destinos_file:
    df_origenes = pd.read_csv(origenes_file)
    df_destinos = pd.read_csv(destinos_file)

    st.subheader("📍 Orígenes")
    st.dataframe(df_origenes)
    st.subheader("🏁 Destinos")
    st.dataframe(df_destinos)

    resultados = []
    m = folium.Map(location=[df_origenes["lat"].mean(), df_origenes["lon"].mean()], zoom_start=9)

    # Marcar orígenes
    for _, o in df_origenes.iterrows():
        folium.Marker([o["lat"], o["lon"]], popup=f"Origen {o['nombre']}", icon=folium.Icon(color="blue")).add_to(m)

    # Calcular mejor origen para cada destino
    for _, d in df_destinos.iterrows():
        best_origin = None
        best_dist = float("inf")
        best_coords = None

        for _, o in df_origenes.iterrows():
            url = f"{OSRM_URL}/{o['lon']},{o['lat']};{d['lon']},{d['lat']}?overview=full&geometries=geojson"
            r = requests.get(url)

            if r.status_code == 200:
                data = r.json()
                if "routes" in data and len(data["routes"]) > 0:
                    dist_km = data["routes"][0]["distance"] / 1000  # metros → km
                    coords = data["routes"][0]["geometry"]["coordinates"]

                    if dist_km < best_dist:
                        best_dist = dist_km
                        best_origin = o
                        best_coords = coords

        coste = best_dist * 0.29 if best_dist != float("inf") else None
        resultados.append({
            "Destino": d["nombre"],
            "Mejor Origen": best_origin["nombre"] if best_origin is not None else "N/A",
            "Distancia (km)": round(best_dist, 2) if best_dist != float("inf") else None,
            "Coste (€)": round(coste, 2) if coste is not None else None
        })

        # Añadir destino
        folium.Marker([d["lat"], d["lon"]], popup=f"Destino {d['nombre']}", icon=folium.Icon(color="red")).add_to(m)

        # Dibujar la mejor ruta
        if best_coords:
            folium.PolyLine([(lat, lon) for lon, lat in best_coords], color="green", weight=3, opacity=0.8).add_to(m)

    # Mostrar resultados
    st.subheader("📊 Tabla resumen")
    df_resultados = pd.DataFrame(resultados)
    st.dataframe(df_resultados)

    st.subheader("🗺️ Mapa de rutas")
    st_folium(m, width=900, height=600)
