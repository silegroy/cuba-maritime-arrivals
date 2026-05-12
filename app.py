import streamlit as st
from db import get_supabase

st.set_page_config(page_title="Test Supabase Data API")

st.title("🔧 Test de conexión a Supabase")
st.write("Probando conexión a la base de datos...")

try:
    supabase = get_supabase()
    response = supabase.table("arrivals").select("*").limit(5).execute()

    st.success("✅ Conectado a Supabase Data API correctamente")
    st.json(response.data)

except Exception as e:
    st.error("❌ Error conectando a Supabase")
    st.code(str(e))

st.stop()
