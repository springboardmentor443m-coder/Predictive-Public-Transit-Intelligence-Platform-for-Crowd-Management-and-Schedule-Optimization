import requests

url = "https://data.ny.gov/resource/5wq4-mkjj.json"

params = {
    "$limit": 5
}

response = requests.get(url, params=params)

print("Status:", response.status_code)
print(response.text[:3000])