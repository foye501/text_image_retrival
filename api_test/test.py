import requests

url = "http://159.135.196.86:12280/streamers"
with open("./20260109-165210.png", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
with open("./20260109-165215.jpeg", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
with open("./20260109-165219.jpeg", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
with open("20260109-165224.png", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
with open("./20260109-165228.png", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
# with open("20260109-165232.png", "rb") as f:
#     files = {"image": f}
#     data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
with open("./20260109-165252.png", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
with open("20260109-165313.png", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
with open("./20260109-165344.jpeg", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
with open("./20260109-165831.jpeg", "rb") as f:
    files = {"image": f}
    data = {"streamer_id": "streamer_005"}
    resp = requests.post(url, files=files, data=data)
print(resp.status_code, resp.json())






