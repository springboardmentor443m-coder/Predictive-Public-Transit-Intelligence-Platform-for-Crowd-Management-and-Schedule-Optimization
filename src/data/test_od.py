import requests

URL = "https://data.ny.gov/resource/jsu2-fbtj.json"

params = {
    "$limit": 5
}

response = requests.get(URL, params=params)

print("Status:", response.status_code)
print(response.text[:5000])
