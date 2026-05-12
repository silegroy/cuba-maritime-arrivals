
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

