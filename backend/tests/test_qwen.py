import sys
import os
import httpx
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import QWEN_API_KEY

def test_qwen_json():
    print("Testing Qwen JSON mode via api.groq.com")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen/qwen3-32b",
        "messages": [{"role": "user", "content": "Reply in JSON: {\"test\": \"value\"}"}],
        "response_format": {"type": "json_object"}
    }
    with httpx.Client() as client:
        try:
            res = client.post(url, headers=headers, json=data, timeout=10.0)
            print("Status:", res.status_code)
            print("Response:", res.text)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    test_qwen_json()
