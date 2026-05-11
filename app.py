import streamlit as st
from db import get_connection

st.title("Comprobación de conexión a Supabase")

try:
    conn = get_connection()
    st.success("✅ Conectado a Supabase correctamente")
    conn.close()
except Exception as e:
    st.error("❌ Error real de PostgreSQL:")
    st.code(str(e))
    st.stop()