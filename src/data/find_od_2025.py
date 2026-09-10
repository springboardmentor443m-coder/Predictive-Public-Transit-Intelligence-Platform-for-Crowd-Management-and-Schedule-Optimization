import requests

url = "https://api.us.socrata.com/api/catalog/v1"

params = {
    "search_context": "data.ny.gov",
    "q": "MTA Subway Origin-Destination Ridership Estimate Beginning 2025"
}

response = requests.get(url, params=params)
response.raise_for_status()

results = response.json()["results"]

for result in results:
    resource = result["resource"]

    print("Name:", resource.get("name"))
    print("Dataset ID:", resource.get("id"))
    print("URL:", result.get("permalink"))
    print("-" * 60)