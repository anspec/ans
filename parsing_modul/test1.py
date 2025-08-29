import requests

url = "https://api.github.com/search/repositories"

params = {"q": "language:html"}

response = requests.get(url, params=params)

print(f"Status code: {response.status_code}")
print(response.json())