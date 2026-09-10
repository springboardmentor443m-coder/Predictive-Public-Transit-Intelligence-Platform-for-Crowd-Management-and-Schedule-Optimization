import requests

URL = "https://data.ny.gov/resource/5wq4-mkjj.json"

params = {
    "$select": "min(transit_timestamp) as min_date, max(transit_timestamp) as max_date"
}

response = requests.get(URL, params=params)

print("Status:", response.status_code)
print(response.text)