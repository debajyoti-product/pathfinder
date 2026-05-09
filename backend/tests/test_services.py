import sys
import os
import httpx
import json

# Ensure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import GEMINI_API_KEY, GROQ_API_KEY

def test_gemini_connectivity():
    """Test Gemini API connectivity (from legacy test3.py)."""
    print("\n--- Testing Gemini Connectivity (Legacy test3.py) ---")
    prompt = "Hello, what model are you?"
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}"
    try:
        with httpx.Client() as client:
            res = client.post(url, json=data, timeout=30)
            print("Status:", res.status_code)
            print(res.text)
    except Exception as e:
        print("Error:", e)

def list_gemini_models():
    """List available Gemini Flash models (from legacy test_model.py)."""
    print("\n--- Listing Gemini Flash Models (Legacy test_model.py) ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        with httpx.Client() as client:
            res = client.get(url, timeout=30)
            data = res.json()
            flash_models = [m["name"].replace("models/", "") for m in data.get("models", []) if "flash" in m["name"].lower()]
            for m in sorted(flash_models):
                print(f" - {m}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_gemini_connectivity()
    list_gemini_models()
