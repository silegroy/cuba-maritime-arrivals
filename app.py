import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt

from config import CUBA_PORTS
from db import get_connection

st.set_page_config(page_title="Arribos Marítimos a Cuba", layout="wide")

st.title("🚢 Arribos Marítimos a Puertos de Cuba")

@st.cache_data
def load_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM arrivals", conn)
    conn.close()
    return df

df = load_data()