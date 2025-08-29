import requests

url = "https://jsonplaceholder.typicode.com/posts"

data = {'title': 'foo', 'body': 'bar', 'userId': 1}

response = requests.post(url, json=data)

print(f"Status code: {response.status_code}")
print(f"ответ - {response.json}")