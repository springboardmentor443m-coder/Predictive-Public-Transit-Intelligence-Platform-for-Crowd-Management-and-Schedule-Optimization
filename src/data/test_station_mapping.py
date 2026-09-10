import requests

URL = "https://data.ny.gov/resource/i9wp-a4ja.json"

params = {
    "$limit": 10
}

response = requests.get(URL, params=params)

print("Status:", response.status_code)
print(response.text[:5000])