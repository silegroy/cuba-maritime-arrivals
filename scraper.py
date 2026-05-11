# scraper.py
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Cuba-Maritime-Research/1.0 (public data)"
}

def scrape_port_arrivals(port_name):
    """
    Scraping pasivo de arribos visibles públicamente
    """
    url = f"https://www.marinetraffic.com/en/ports/{port_name.replace(' ', '-')}"
    resp = requests.get(url, headers=HEADERS, timeout=20)

    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    arrivals = []

    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) >= 4:
            arrivals.append({
                "vessel_name": cells[0].get_text(strip=True),
                "origin_port": cells[2].get_text(strip=True)
            })

    return arrivals