import requests

URL = "https://data.ny.gov/resource/y2qv-fytt.json"

params = {
    "$select": "date_trunc_ymd(timestamp) as date, count(*) as rows",
    "$group": "date",
    "$order": "date"
}

response = requests.get(URL, params=params)
response.raise_for_status()

data = response.json()

print("Available dates:")

for row in data:
    print(row)