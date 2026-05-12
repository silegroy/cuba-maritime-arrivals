from datetime import date
from db import get_supabase

def run_test_scraper():
    supabase = get_supabase()

    sample_arrivals = [
        {
            "vessel_name": "MV Caribbean Trader",
            "arrival_date": date.today().isoformat(),
            "origin_country": "Mexico",
            "destination_port": "Havana",
            "vessel_type": "General Cargo"
        },
        {
            "vessel_name": "MV Atlantic Star",
            "arrival_date": date.today().isoformat(),
            "origin_country": "Panama",
            "destination_port": "Mariel",
            "vessel_type": "Container"
        },
        {
            "vessel_name": "MT Gulf Energy",
            "arrival_date": date.today().isoformat(),
            "origin_country": "USA",
            "destination_port": "Cienfuegos",
            "vessel_type": "Tanker"
        }
    ]

    response = supabase.table("arrivals").insert(sample_arrivals).execute()
    return response