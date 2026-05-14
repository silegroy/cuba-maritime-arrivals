# ----------------------------
# IMPORTS
# ----------------------------
# Streamlit: framework web
import streamlit as st

# Pandas: manejo de datos
import pandas as pd

# Pydeck: mapas
import pydeck as pdk

# Altair: gráficos
import altair as alt

# Cliente Supabase (Data API)
from db import get_supabase

# Coordenadas de puertos
from config import CUBA_PORTS

# Scraper que inserta datos
from scraper_real import run_real_scraper


# ----------------------------
# CONFIGURACIÓN INICIAL
# ----------------------------
# Configura la página de Streamlit
st.set_page_config(
    page_title="🚢 Arribos Marítimos a Cuba",
    layout="wide"
)

# Título principal
st.title("🚢 Arribos Marítimos a Puertos de Cuba")

# Descripción
st.caption("Datos obtenidos vía Supabase Data API (REST)")


# ----------------------------
# BOTÓN PARA EJECUTAR SCRAPER
# ----------------------------
# Permite insertar nuevos datos manualmente
if st.button("🚢 Ejecutar scraper real"):
    run_real_scraper()  # Llama al scraper
    st.success("Scraper ejecutado correctamente")
    st.cache_data.clear()  # Limpia caché para ver nuevos datos


# ----------------------------
# MAPA (SE MUESTRA RÁPIDO)
# ----------------------------
# No depende de la base de datos → mejora UX
st.subheader("📍 Puertos de Cuba")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=CUBA_PORTS,  # Datos estáticos
    get_position="[lon, lat]",  # Coordenadas
    get_radius=7000,  # Tamaño del punto
    get_color=[200, 30, 0],  # Color rojo
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
# CARGA DE DATOS OPTIMIZADA
# ----------------------------
# Conexión a Supabase
supabase = get_supabase()

# Cachea la consulta (no se ejecuta siempre)
@st.cache_data(ttl=600)
def load_data():
    response = (
        supabase
        .table("arrivals")
        .select(  # Solo columnas necesarias → más rápido
            "vessel_name, vessel_type, origin_country, destination_port, arrival_date"
        )
        .order("arrival_date", desc=True)
        .limit(500)  # Limita resultados
        .execute()
    )

    # Convierte a DataFrame
    df = pd.DataFrame(response.data)
    return df


# Indicador de carga
with st.spinner("Cargando datos..."):
    df = load_data()


# ----------------------------
# LIMPIEZA DE DATOS
# ----------------------------
# Normaliza nombres de columnas
df.columns = [c.lower() for c in df.columns]

# Convierte fechas
df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")

# Elimina duplicados
df = df.drop_duplicates(
    subset=["vessel_name", "arrival_date", "destination_port"]
)


# ----------------------------
# FILTROS INTERACTIVOS
# ----------------------------
st.subheader("🔎 Filtros")

col1, col2, col3 = st.columns(3)

# Filtro por país
with col1:
    countries = st.multiselect(
        "País de origen",
        sorted(df["origin_country"].dropna().unique()),
        default=df["origin_country"].dropna().unique()
    )

# Filtro por puerto
with col2:
    ports = st.multiselect(
        "Puerto destino",
        sorted(df["destination_port"].dropna().unique()),
        default=df["destination_port"].dropna().unique()
    )

# Filtro por tipo de barco
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
# KPIs (INDICADORES RÁPIDOS)
# ----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("🚢 Total barcos", len(df_filtered))
col2.metric("🌍 Países activos", df_filtered["origin_country"].nunique())
col3.metric("⚓ Puertos activos", df_filtered["destination_port"].nunique())


# ----------------------------
# ANÁLISIS CON GRÁFICOS PASTEL
# ----------------------------
st.subheader("📊 Análisis de arribos")

if df_filtered.empty:
    st.warning("No hay datos con estos filtros")

else:

    # -------------------------
    # 1. PASTEL: BARCOS POR PAÍS
    # -------------------------
    df_country = (
        df_filtered.groupby("origin_country")
        .size()
        .reset_index(name="arrivals")
    )

    chart_country = alt.Chart(df_country).mark_arc().encode(
        theta="arrivals:Q",  # tamaño del sector
        color="origin_country:N",
        tooltip=[
            alt.Tooltip("origin_country:N", title="País"),
            alt.Tooltip("arrivals:Q", title="Cantidad de barcos")
        ]
    )

    st.markdown("### 🌎 Distribución de barcos por país")
    st.altair_chart(chart_country, use_container_width=True)


    # -------------------------
    # 2. PASTEL: TIPO DE BUQUE
    # -------------------------
    df_type = (
        df_filtered.groupby("vessel_type")
        .size()
        .reset_index(name="arrivals")
    )

    chart_type = alt.Chart(df_type).mark_arc().encode(
        theta="arrivals:Q",
        color="vessel_type:N",
        tooltip=[
            alt.Tooltip("vessel_type:N", title="Tipo de buque"),
            alt.Tooltip("arrivals:Q", title="Cantidad de barcos")
        ]
    )

    st.markdown("### 🚢 Distribución por tipo de buque")
    st.altair_chart(chart_type, use_container_width=True)


    # -------------------------
    # 3. TONELAJE ESTIMADO
    # -------------------------
    tonnage_map = {
        "Container": 50000,
        "Tanker": 80000,
        "General Cargo": 20000
    }

    df_filtered["estimated_tonnage"] = df_filtered["vessel_type"].map(tonnage_map)

    df_ton = (
        df_filtered.groupby("origin_country")["estimated_tonnage"]
        .sum()
        .reset_index()
    )

    chart_ton = alt.Chart(df_ton).mark_arc().encode(
        theta="estimated_tonnage:Q",
        color="origin_country:N",
        tooltip=[
            alt.Tooltip("origin_country:N", title="País"),
            alt.Tooltip("estimated_tonnage:Q", title="Tonelaje estimado")
        ]
    )

    st.markdown("### ⚖️ Distribución de tonelaje estimado")
    st.altair_chart(chart_ton, use_container_width=True)


    # -------------------------
    # 4. EVOLUCIÓN POR AÑO
    # -------------------------
    df_filtered["year"] = df_filtered["arrival_date"].dt.year

    df_year = (
        df_filtered.groupby("year")
        .size()
        .reset_index(name="arrivals")
    )

    chart_year = alt.Chart(df_year).mark_bar().encode(
        x=alt.X("year:O", title="Año de llegada"),
        y=alt.Y("arrivals:Q", title="Cantidad de barcos"),
        tooltip=["year", "arrivals"]
    )

    st.markdown("### 📈 Evolución de arribos por año")
    st.altair_chart(chart_year, use_container_width=True)


# ----------------------------
# TABLA FINAL
# ----------------------------
st.subheader("📋 Detalle de arribos")
st.dataframe(df_filtered, use_container_width=True)