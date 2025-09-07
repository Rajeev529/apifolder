import requests

# url = "https://bajajapi3.onrender.com/api/v1/hackrx/run"
# url = "http://127.0.0.1:8000/answer/ee410713-596f-4cda-8cfe-0ffff841c1d6/"
# url = "http://127.0.0.1:8000/answer/a8bf2e98-89fa-4b69-9d0b-bb0e36ffd64d/"
url = "http://127.0.0.1:8000/answer/e9d6457c-5f36-4072-b482-40f02ef6cc45/"
payload = {
    "query": "who is akshay kumar"
}
print("now")
res = requests.post(url, json=payload)
print(res.status_code)
print(res.json())
