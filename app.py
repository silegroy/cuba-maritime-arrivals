# ----------------------------
# IMPORTS
# ----------------------------
import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt

from db import get_supabase
from config import CUBA_PORTS
from scraper_real import run_real_scraper


# ----------------------------
# CONFIGURACIÓN GENERAL
# ----------------------------
st.set_page_config(
    page_title="🚢 Arribos Marítimos a Cuba",
    layout="wide"
)

st.title("🚢 Arribos Marítimos a Puertos de Cuba")
st.caption("Dashboard de inteligencia marítima (OSINT)")


# ----------------------------
# BOTÓN SCRAPER
# ----------------------------
if st.button("🚢 Ejecutar scraper real"):
    run_real_scraper()
    st.success("Scraper ejecutado correctamente")
    st.cache_data.clear()


# ----------------------------
# CONEXIÓN Y CARGA DE DATOS
# ----------------------------
supabase = get_supabase()

@st.cache_data(ttl=600)
def load_data():
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
    return pd.DataFrame(response.data)


with st.spinner("Cargando datos..."):
    df = load_data()


# ----------------------------
# LIMPIEZA DE DATOS
# ----------------------------
df.columns = [c.lower() for c in df.columns]
df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")

# eliminar duplicados
df = df.drop_duplicates(
    subset=["vessel_name", "arrival_date", "destination_port"]
)


# ----------------------------
# FILTROS INTERACTIVOS
# ----------------------------
st.subheader("🔎 Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    countries = st.multiselect(
        "País",
        sorted(df["origin_country"].dropna().unique()),
        default=df["origin_country"].dropna().unique()
    )

with col2:
    ports = st.multiselect(
        "Puerto",
        sorted(df["destination_port"].dropna().unique()),
        default=df["destination_port"].dropna().unique()
    )

with col3:
    vessel_types = st.multiselect(
        "Tipo de buque",
        sorted(df["vessel_type"].dropna().unique()),
        default=df["vessel_type"].dropna().unique()
    )


# ----------------------------
# FILTRO POR FECHAS
# ----------------------------
min_date = df["arrival_date"].min()
max_date = df["arrival_date"].max()

start_date, end_date = st.date_input(
    "📅 Rango de fechas",
    [min_date, max_date]
)


# Aplicar filtros
df_filtered = df[
    df["origin_country"].isin(countries) &
    df["destination_port"].isin(ports) &
    df["vessel_type"].isin(vessel_types)
]

df_filtered = df_filtered[
    (df_filtered["arrival_date"] >= pd.to_datetime(start_date)) &
    (df_filtered["arrival_date"] <= pd.to_datetime(end_date))
]


# ----------------------------
# KPIs
# ----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("🚢 Total barcos", len(df_filtered))
col2.metric("🌍 Países activos", df_filtered["origin_country"].nunique())
col3.metric("⚓ Puertos activos", df_filtered["destination_port"].nunique())


# ----------------------------
# MAPA CON VOLUMEN
# ----------------------------
st.subheader("📍 Actividad por puerto")

df_map = (
    df_filtered.groupby("destination_port")
    .size()
    .reset_index(name="barcos")
)

df_map = pd.merge(
    df_map,
    pd.DataFrame(CUBA_PORTS),
    left_on="destination_port",
    right_on="name"
)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position="[lon, lat]",
    get_radius="barcos * 3000",
    get_fill_color="[255, 140, 0]",
    pickable=True
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=22, longitude=-80, zoom=5),
        tooltip={"text": "{name} - Barcos: {barcos}"}
    )
)


# ----------------------------
# MAPA DE RUTAS
# ----------------------------
st.subheader("🧭 Rutas marítimas")

country_coords = {
    "USA": [-95, 37],
    "Mexico": [-102, 23],
    "Panama": [-80, 8],
    "Venezuela": [-66, 7]
}

routes = []

for _, row in df_filtered.iterrows():
    origin = row["origin_country"]
    destination = row["destination_port"]

    if origin in country_coords:
        port_data = next((p for p in CUBA_PORTS if p["name"] == destination), None)

        if port_data:
            routes.append({
                "from_lon": country_coords[origin][0],
                "from_lat": country_coords[origin][1],
                "to_lon": port_data["lon"],
                "to_lat": port_data["lat"]
            })

layer_routes = pdk.Layer(
    "LineLayer",
    data=routes,
    get_source_position="[from_lon, from_lat]",
    get_target_position="[to_lon, to_lat]",
    get_color="[0, 120, 255]",
    get_width=2
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer_routes],
        initial_view_state=pdk.ViewState(latitude=20, longitude=-75, zoom=3)
    )
)


# ----------------------------
# ANÁLISIS
# ----------------------------
st.subheader("📊 Análisis")

if not df_filtered.empty:

    # barcos por país
    df_country = (
        df_filtered.groupby("origin_country")
        .size()
        .reset_index(name="barcos")
    )

    chart_country = alt.Chart(df_country).mark_arc().encode(
        theta="barcos:Q",
        color="origin_country:N",
        tooltip=["origin_country", "barcos"]
    )

    # tipo de buque
    df_type = (
        df_filtered.groupby("vessel_type")
        .size()
        .reset_index(name="barcos")
    )

    chart_type = alt.Chart(df_type).mark_arc().encode(
        theta="barcos:Q",
        color="vessel_type:N",
        tooltip=["vessel_type", "barcos"]
    )

    # tonelaje estimado
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
        color="origin_country:N",
        tooltip=["origin_country", "tonelaje"]
    )

    # evolución
    df_filtered["year"] = df_filtered["arrival_date"].dt.year

    df_year = (
        df_filtered.groupby(["year", "origin_country"])
        .size()
        .reset_index(name="barcos")
    )

    chart_year = alt.Chart(df_year).mark_line(point=True).encode(
        x="year:O",
        y="barcos:Q",
        color="origin_country:N",
        tooltip=["year", "origin_country", "barcos"]
    )

    # visual dashboard
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🌎 País")
        st.altair_chart(chart_country, use_container_width=True)

    with col2:
        st.markdown("### 🚢 Tipo")
        st.altair_chart(chart_type, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### ⚖️ Tonelaje")
        st.altair_chart(chart_ton, use_container_width=True)

    with col4:
        st.markdown("### 📈 Evolución")
        st.altair_chart(chart_year, use_container_width=True)


# ----------------------------
# ALERTAS AVANZADAS
# ----------------------------
st.subheader("🚨 Alertas inteligentes")

alerts = []

if not df_filtered.empty:

    total = len(df_filtered)

    df_country = (
        df_filtered.groupby("origin_country")
        .size()
        .reset_index(name="barcos")
    )

    # país dominante
    for _, row in df_country.iterrows():
        if row["barcos"] / total > 0.5:
            alerts.append(f"🚨 Dominancia de {row['origin_country']}")

    # tankers
    tankers = df_filtered[df_filtered["vessel_type"] == "Tanker"]
    if len(tankers) > total * 0.3:
        alerts.append(f"⛽ Alta concentración de Tankers ({len(tankers)})")

    # actividad reciente
    recent = df_filtered[df_filtered["arrival_date"] > (pd.Timestamp.today() - pd.Timedelta(days=7))]
    if len(recent) > total * 0.5:
        alerts.append("📈 Incremento reciente de actividad")

# mostrar
if alerts:
    for alert in alerts:
        st.warning(alert)
else:
    st.success("✅ Sin anomalías detectadas")