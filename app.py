
import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt

from db import get_supabase
from config import CUBA_PORTS
from scraper_real import run_real_scraper


st.set_page_config(
    page_title="🚢 Arribos Marítimos a Cuba",
    layout="wide"
)

st.title("🚢 Arribos Marítimos a Puertos de Cuba")
st.caption("Datos obtenidos vía Supabase Data API (REST)")

# Botón del scraper (manual, controlado)
if st.button("🚢 Ejecutar scraper real"):
    run_real_scraper()
    st.success("Scraper ejecutado correctamente")
    st.cache_data.clear()

st.subheader("📍 Puertos de Cuba")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=CUBA_PORTS,
    get_position="[lon, lat]",
    get_radius=7000,
    get_color=[200, 30, 0],
)

view_state = pdk.ViewState(
    latitude=22,
    longitude=-80,
    zoom=5,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state
    )
)

# ----------------------------
# CARGA OPTIMIZADA DE DATOS
# ----------------------------

supabase = get_supabase()

@st.cache_data(ttl=600)
def load_arrivals():
    response = (
        supabase
        .table("arrivals")
        .select(
            "vessel_name, vessel_type, origin_country, destination_port, arrival_date"
        )
        .order("arrival_date", desc=True)
        .limit(500)
        .execute()
    )
    df = pd.DataFrame(response.data)
    return df
st.subheader("📊 Análisis de arribos")

with st.spinner("Cargando datos..."):
    df = load_arrivals()

# Normalizar columnas
df.columns = [c.lower() for c in df.columns]

if "arrival_date" in df.columns:
    df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")

if df.empty:
    st.info("Aún no hay registros.")
else:
    # Arribos por país
    df_country = (
        df.dropna(subset=["origin_country"])
        .groupby("origin_country")
        .size()
        .reset_index(name="arrivals")
    )

    st.markdown("**Arribos por país**")
    st.altair_chart(
        alt.Chart(df_country).mark_bar().encode(
            x="origin_country:N",
            y="arrivals:Q"
        ),
        use_container_width=True
    )

df_country = (
    df.dropna(subset=["origin_country"])
    .groupby("origin_country")
    .size()
    .reset_index(name="arrivals")
    .sort_values("arrivals", ascending=False)
)

chart_country = alt.Chart(df_country).mark_bar().encode(
    x=alt.X("arrivals:Q", title="Cantidad de barcos"),
    y=alt.Y("origin_country:N", sort='-x', title="País"),
    tooltip=["origin_country", "arrivals"]
)

st.markdown("### 🌎 Barcos por país de origen")
st.altair_chart(chart_country, use_container_width=True)

df_type = (
    df.dropna(subset=["origin_country", "vessel_type"])
    .groupby(["origin_country", "vessel_type"])
    .size()
    .reset_index(name="arrivals")
)

chart_type = alt.Chart(df_type).mark_bar().encode(
    x="origin_country:N",
    y="arrivals:Q",
    color="vessel_type:N",
    tooltip=["origin_country", "vessel_type", "arrivals"]
)

st.markdown("### 🚢 País vs tipo de buque")
st.altair_chart(chart_type, use_container_width=True)
