# db.py
import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        port=int(os.environ["DB_PORT"]),   # ✅ CAST OBLIGATORIO
        sslmode="require"                  # ✅ REQUERIDO POR SUPABASE
    )