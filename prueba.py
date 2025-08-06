import requests
from datetime import datetime, timedelta


url = f"https://date.nager.at/api/v3/PublicHolidays/2025/CO"
response = requests.get(url)
if response.status_code == 200:
    print(response.json())