
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
