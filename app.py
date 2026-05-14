# ----------------------------
# IMPORTS
# ----------------------------
import streamlit as st               # Framework web
import pandas as pd                # Manipulación de datos
import pydeck as pdk               # Mapas
import altair as alt               # Gráficos

from db import get_supabase         # Cliente Supabase
from config import CUBA_PORTS       # Coordenadas de puertos
from scraper_real import run_real_scraper  # Scraper

# ----------------------------
# CONFIGURACIÓN
# ----------------------------
st.set_page_config(
    page_title="🚢 Arribos Marítimos a Cuba",
    layout="wide"
)

st.title("🚢 Arribos Marítimos a Puertos de Cuba")
st.caption("Visualización interactiva de tráfico marítimo")

# ----------------------------
# BOTÓN SCRAPER
# ----------------------------
if st.button("🚢 Ejecutar scraper real"):
    run_real_scraper()
    st.success("Scraper ejecutado correctamente")
    st.cache_data.clear()

# ----------------------------
# MAPA
# ----------------------------
st.subheader("📍 Puertos de Cuba")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=CUBA_PORTS,
    get_position="[lon, lat]",
    get_radius=7000,
    get_color=[200, 30, 0]
)

view_state = pdk.ViewState(latitude=22, longitude=-80, zoom=5)

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))


# ----------------------------
# CARGA DE DATOS OPTIMIZADA
# ----------------------------
supabase = get_supabase()

@st.cache_data(ttl=600)
def load_data():
    response = (
        supabase
        .table("arrivals")
        .select("vessel_name, vessel_type, origin_country, destination_port, arrival_date")
        .order("arrival_date", desc=True)
        .limit(500)
        .execute()
    )

    return pd.DataFrame(response.data)

with st.spinner("Cargando datos..."):
    df = load_data()

# ----------------------------
# LIMPIEZA
# ----------------------------
df.columns = [c.lower() for c in df.columns]

df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")

# QUITA DUPLICADOS → evita conteos falsos
df = df.drop_duplicates(
    subset=["vessel_name", "arrival_date", "destination_port"]
)

# ----------------------------
# FILTROS
# ----------------------------
st.subheader("🔎 Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    countries = st.multiselect(
        "País de origen",
        sorted(df["origin_country"].dropna().unique()),
        default=df["origin_country"].dropna().unique()
    )

with col2:
    ports = st.multiselect(
        "Puerto destino",
        sorted(df["destination_port"].dropna().unique()),
        default=df["destination_port"].dropna().unique()
    )

with col3:
    vessel_types = st.multiselect(
        "Tipo de buque",
        sorted(df["vessel_type"].dropna().unique()),
        default=df["vessel_type"].dropna().unique()
    )

# Aplicar filtros
df_filtered = df[
    df["origin_country"].isin(countries) &
    df["destination_port"].isin(ports) &
    df["vessel_type"].isin(vessel_types)
]

# ----------------------------
# KPIs (ahora claros)
# ----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("🚢 Total barcos", len(df_filtered))
col2.metric("🌍 Países activos", df_filtered["origin_country"].nunique())
col3.metric("⚓ Puertos activos", df_filtered["destination_port"].nunique())


# ----------------------------
# ANÁLISIS
# ----------------------------
st.subheader("📊 Análisis de arribos")

if df_filtered.empty:
    st.warning("No hay datos con estos filtros")

else:

    # -------------------------
    # ✅ 1. DISTRIBUCIÓN POR PAÍS
    # -------------------------
    df_country = (
        df_filtered.groupby("origin_country")
        .size()
        .reset_index(name="barcos")
    )

    chart_country = alt.Chart(df_country).mark_arc().encode(
        theta=alt.Theta("barcos:Q", title="Cantidad de barcos"),
        color=alt.Color("origin_country:N", title="País"),
        tooltip=[
            alt.Tooltip("origin_country:N", title="País"),
            alt.Tooltip("barcos:Q", title="Cantidad de barcos")
        ]
    )

    st.markdown("### 🌎 Distribución de barcos por país")
    st.altair_chart(chart_country, use_container_width=True)


    # -------------------------
    # ✅ 2. DISTRIBUCIÓN POR TIPO DE BUQUE
    # -------------------------
    df_type = (
        df_filtered.groupby("vessel_type")
        .size()
        .reset_index(name="barcos")
    )

    chart_type = alt.Chart(df_type).mark_arc().encode(
        theta="barcos:Q",
        color=alt.Color("vessel_type:N", title="Tipo de buque"),
        tooltip=[
            alt.Tooltip("vessel_type:N", title="Tipo"),
            alt.Tooltip("barcos:Q", title="Número de barcos")
        ]
    )

    st.markdown("### 🚢 Distribución por tipo de buque")
    st.altair_chart(chart_type, use_container_width=True)


    # -------------------------
    # ✅ 3. TONELAJE ESTIMADO
    # -------------------------
    tonnage_map = {
        "Container": 50000,
        "Tanker": 80000,
        "General Cargo": 20000
    }

    df_filtered["tonelaje"] = df_filtered["vessel_type"].map(tonnage_map)

    df_ton = (
        df_filtered.groupby("origin_country")["tonelaje"]
        .sum()
        .reset_index()
    )

    chart_ton = alt.Chart(df_ton).mark_arc().encode(
        theta="tonelaje:Q",
        color=alt.Color("origin_country:N"),
        tooltip=[
            alt.Tooltip("origin_country:N", title="País"),
            alt.Tooltip("tonelaje:Q", title="Tonelaje estimado")
        ]
    )

    st.markdown("### ⚖️ Distribución de carga estimada")
    st.altair_chart(chart_ton, use_container_width=True)


    # -------------------------
    # ✅ 4. EVOLUCIÓN POR AÑO (CORREGIDA)
    # -------------------------
    df_filtered["year"] = df_filtered["arrival_date"].dt.year

    df_year = (
        df_filtered.groupby(["year", "origin_country"])
        .size()
        .reset_index(name="barcos")
    )

    chart_year = alt.Chart(df_year).mark_line(point=True).encode(
        x=alt.X("year:O", title="Año real de llegada"),
        y=alt.Y("barcos:Q", title="Cantidad de barcos"),
        color=alt.Color("origin_country:N", title="País"),
        tooltip=["year", "origin_country", "barcos"]
    )

    st.markdown("### 📈 Evolución real de arribos por país")
    st.altair_chart(chart_year, use_container_width=True)