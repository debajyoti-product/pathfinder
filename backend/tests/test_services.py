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

def test_usage_tracker_graceful_fail():
    from services.usage_tracker import is_over_limit, USAGE_FILE
    import unittest.mock as mock
    with mock.patch("os.path.exists", side_effect=Exception("Mocked I/O Error")):
        result = is_over_limit("serper")
        assert result is False, "is_over_limit should return False on I/O error"
    print("test_usage_tracker_graceful_fail passed.")

def test_usage_tracker_threshold():
    from services.usage_tracker import is_over_limit, USAGE_FILE
    import unittest.mock as mock
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d")
    
    mock_data = {
        now: {
            "serper": 800  # 80% of 1000 limit
        }
    }
    
    with mock.patch("os.path.exists", return_value=True), \
         mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(mock_data))):
        result_80 = is_over_limit("serper")
        assert result_80 is False, "is_over_limit should return False at 80%"
        
    mock_data[now]["serper"] = 1000 # 100%
    with mock.patch("os.path.exists", return_value=True), \
         mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(mock_data))):
        result_100 = is_over_limit("serper")
        assert result_100 is True, "is_over_limit should return True at 100%"
        
    print("test_usage_tracker_threshold passed.")

def test_serper_graceful_degradation():
    from services.serper_client import SerperClient
    import unittest.mock as mock
    
    with mock.patch("services.serper_client.is_over_limit", return_value=True):
        client = SerperClient()
        result = client.search("test")
        assert result.get("limited") is True, "Should return limited flag"
        assert result.get("organic") == [], "Organic should be empty"
        assert "error" in result, "Error key should be present"
        
    print("test_serper_graceful_degradation passed.")

if __name__ == "__main__":
    # test_gemini_connectivity()
    # list_gemini_models()
    test_usage_tracker_graceful_fail()
    test_usage_tracker_threshold()
    test_serper_graceful_degradation()
