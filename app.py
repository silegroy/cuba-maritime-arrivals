import streamlit as st
from db import get_connection

st.set_page_config(page_title="Cuba Maritime Arrivals - Test DB")

st.title("🔧 Test de conexión a Supabase")

st.write("Probando conexión a la base de datos...")

try:
    conn = get_connection()
    st.success("✅ Conectado a Supabase correctamente")
    conn.close()
except Exception as e:
    st.error("❌ Error conectando a Supabase")
    st.code(str(e))

st.stop()