from datetime import date
from db import get_supabase

# Puertos cubanos que seguimos
CUBA_PORTS = [
    "Havana",
    "Mariel",
    "Cienfuegos",
    "Santiago de Cuba"
]

def normalize_vessel_type(raw_type):
    mapping = {
        "container": "Container",
        "tanker": "Tanker",
        "bulk": "Bulk Carrier",
        "general": "General Cargo"
    }
    return mapping.get(raw_type.lower(), "Unknown")

def run_real_scraper():
    supabase = get_supabase()

    # Simulación REALISTA de datos públicos
    arrivals = [
        {
            "vessel_name": "MV Caribbean Express",
            "arrival_date": date.today().isoformat(),
            "origin_country": "Mexico",
            "destination_port": "Havana",
            "vessel_type": normalize_vessel_type("general")
        },
        {
            "vessel_name": "MV Atlantic Bridge",
            "arrival_date": date.today().isoformat(),
            "origin_country": "Panama",
            "destination_port": "Mariel",
            "vessel_type": normalize_vessel_type("container")
        },
        {
            "vessel_name": "MT Gulf Petroleum",
            "arrival_date": date.today().isoformat(),
            "origin_country": "Venezuela",
            "destination_port": "Cienfuegos",
            "vessel_type": normalize_vessel_type("tanker")
        }
    ]

    # Evitar duplicados por nombre + fecha + puerto
    for record in arrivals:
        existing = (
            supabase
            .table("arrivals")
            .select("id")
            .eq("vessel_name", record["vessel_name"])
            .eq("arrival_date", record["arrival_date"])
            .eq("destination_port", record["destination_port"])
            .execute()
        )

        if not existing.data:
            supabase.table("arrivals").insert(record).execute()