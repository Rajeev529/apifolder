import requests

# url = "https://bajajapi3.onrender.com/api/v1/hackrx/run"
# url = "http://127.0.0.1:8000/answer/ee410713-596f-4cda-8cfe-0ffff841c1d6/"
# url = "http://127.0.0.1:8000/answer/a8bf2e98-89fa-4b69-9d0b-bb0e36ffd64d/"
url = "http://127.0.0.1:8000/answer/0daadc15-7df4-4935-bdf5-80307ee14a8f/"
payload = {
    "query": "topic : Economics of Power Generation"
}
print("now")
res = requests.post(url, json=payload)
print(res.status_code)
print(res.json())
