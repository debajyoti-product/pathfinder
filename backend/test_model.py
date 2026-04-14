import httpx

API_KEY = "AIzaSyC4xUcAPrZ5weBz_fJsw9xsBxs2IXCfULk"

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
with httpx.Client() as client:
    res = client.get(url, timeout=30)
    data = res.json()
    
    flash_models = [m["name"].replace("models/", "") for m in data.get("models", []) if "flash" in m["name"].lower()]
    for m in sorted(flash_models):
        print(m)
