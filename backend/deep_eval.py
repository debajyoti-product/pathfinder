import httpx

with open("valid.pdf", "rb") as f:
    res = httpx.post("http://127.0.0.1:8000/api/parse-resume", files={"file": f}, timeout=60)
    print("Status:", res.status_code)
    print("Body:", res.text)
