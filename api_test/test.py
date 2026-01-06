import requests

url = "http://159.135.196.86:12280/streamers"
with open("./4-9.png", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_001"}
    resp = requests.post(url, files=files, data=data)

print(resp.status_code, resp.json())





