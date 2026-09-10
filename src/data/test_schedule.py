import requests

URL = "https://data.ny.gov/resource/q9nv-uegs.json"

params = {
    "$limit": 5
}

response = requests.get(URL, params=params)

print("Status:", response.status_code)
print(response.text[:5000])