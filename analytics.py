# analytics.py
from db import get_connection

def save_arrival(arrival, destination):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO arrivals (
            vessel_name,
            origin_port,
            destination_port,
            arrival_date
        )
        SELECT %s, %s, %s, CURRENT_DATE
        WHERE NOT EXISTS (
            SELECT 1 FROM arrivals
            WHERE vessel_name = %s
            AND destination_port = %s
            AND arrival_date = CURRENT_DATE
        )
    """, (
        arrival["vessel_name"],
        arrival["origin_port"],
        destination,
        arrival["vessel_name"],
        destination
    ))

    conn.commit()
    cur.close()
    conn.close()