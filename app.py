import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt

from db import get_supabase
from config import CUBA_PORTS
#from scraper_test import run_test_scraper
from scraper_real import run_real_scraper


# ----------------------------
# Configuración general
# ----------------------------
st.set_page_config(
    page_title="🚢 Arribos Marítimos a Cuba",
    layout="wide"
)

st.title("🚢 Arribos Marítimos a Puertos de Cuba")
# if st.button("Insertar datos de prueba"):
#     run_test_scraper()
#     st.success("Datos de prueba insertados")
#     st.cache_data.clear()
if st.button("🚢 Ejecutar scraper real"):
    run_real_scraper()
    st.success("Scraper ejecutado correctamente")
    st.cache_data.clear()
st.caption("Datos obtenidos vía Supabase Data API (REST)")


# ----------------------------
# Conexión Supabase
# ----------------------------
supabase = get_supabase()

@st.cache_data(ttl=300)
def load_data():
    response = (
        supabase
        .table("arrivals")
        .select("*")
        .order("arrival_date", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data)

df = load_data()

# ----------------------------
# MAPA DE PUERTOS
# ----------------------------
st.subheader("📍 Puertos de Cuba")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=CUBA_PORTS,
    get_position="[lon, lat]",
    get_radius=7000,
    get_color=[200, 30, 0],
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=22,
    longitude=-80,
    zoom=5,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}"}
    )
)

# ----------------------------
# SECCIÓN DE ANÁLISIS
# ----------------------------
st.subheader("📊 Análisis de arribos")

if df.empty:
    st.info("Aún no hay registros en la base de datos.")
else:
    # -------- Arribos por país --------
    if "origin_country" in df.columns:
        st.markdown("**Arribos por país de origen**")

        df_country = (
            df.groupby("origin_country")
            .size()
            .reset_index(name="arrivals")
        )

        chart_country = alt.Chart(df_country).mark_bar().encode(
            x=alt.X("origin_country:N", title="País de origen"),
            y=alt.Y("arrivals:Q", title="Número de arribos"),
            tooltip=["origin_country", "arrivals"]
        )

