import httpx
from config import GEMINI_API_KEY
import json

prompt = "Hello, what model are you?"
data = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseMimeType": "application/json"}
}

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}"
print("Testing gemini-flash-lite-latest...")
try:
    with httpx.Client() as client:
        res = client.post(url, json=data, timeout=30)
        print("Status", res.status_code)
        print(res.text)
except Exception as e:
    print("Error:", e)
