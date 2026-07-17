import sys
import os
import httpx
import json
import asyncio

# Ensure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import SERPER_API_KEY, FIRECRAWL_API_KEY

def test_job_discovery_serper():
    """Test job discovery via Serper (from legacy test_pipeline.py)."""
    print("\n--- Testing Serper Job Discovery (Legacy test_pipeline.py) ---")
    url = 'https://google.serper.dev/search'
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    payload = {'q': 'site:linkedin.com/jobs/view "Product Manager" "India"'}
    try:
        with httpx.Client() as client:
            res = client.post(url, headers=headers, json=payload, timeout=30)
            data = res.json()
            organic = data.get('organic', [])
            print(f"Found {len(organic)} LinkedIn results.")
            for item in organic[:2]:
                print(f"  - {item.get('link')}")
    except Exception as e:
        print(f"Error: {e}")

def test_firecrawl_scraping():
    """Test Firecrawl scraping logic (from legacy test_pipeline.py)."""
    print("\n--- Testing Firecrawl Scraping (Legacy test_pipeline.py) ---")
    if not FIRECRAWL_API_KEY:
        print("Skipping: FIRECRAWL_API_KEY missing.")
        return
        
    # Using a dummy URL for test
    test_url = "https://boards.greenhouse.io/openai/jobs/4241604004" 
    from firecrawl import V1FirecrawlApp
    fc = V1FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    try:
        result = fc.scrape_url(test_url, params={"formats": ["markdown"], "onlyMainContent": True})
        md = result.get("markdown", "")
        print(f"Scrape successful. Content length: {len(md)}")
        print(f"Snippet: {md[:200]}...")
    except Exception as e:
        print(f"Scrape Error: {e}")

def test_resume_upload_integration():
    """Test full resume upload and parsing endpoint (from legacy verify_upload.py)."""
    print("\n--- Testing Resume Upload Integration (Legacy verify_upload.py) ---")
    url = "http://127.0.0.1:8000/api/parse-resume"
    pdf_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "valid.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Skipping: {pdf_path} not found.")
        return

    try:
        files = {'file': ('valid.pdf', open(pdf_path, 'rb'), 'application/pdf')}
        response = httpx.post(url, files=files, timeout=35.0)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
        else:
            print(f"Failed: {response.text}")
    except Exception as e:
        print(f"Connection Error (is server running?): {e}")

def test_expired_jd_filter():
    """Test that the expired phrases deterministic check works."""
    print("\n--- Testing Expired JD Filter ---")
    from main import EXPIRED_PHRASES
    
    expired_jd = "About the role: this job is closed. Thank you."
    active_jd = "About the role: we are actively hiring for this position."
    
    jd_lower_expired = expired_jd.lower()
    is_expired_true = any(phrase in jd_lower_expired for phrase in EXPIRED_PHRASES)
    assert is_expired_true is True, "Should flag expired JD"
    
    jd_lower_active = active_jd.lower()
    is_expired_false = any(phrase in jd_lower_active for phrase in EXPIRED_PHRASES)
    assert is_expired_false is False, "Should not flag active JD"
    print("test_expired_jd_filter passed.")

def test_location_mismatch_filter():
    """Test deterministic location matching logic."""
    print("\n--- Testing Location Mismatch Filter ---")
    from main import is_location_mismatch
    
    # Matching cases (should return False)
    assert is_location_mismatch("Bangalore, India", "India") is False
    assert is_location_mismatch("India", "Bangalore") is False
    assert is_location_mismatch("New York, NY", "New York") is False
    assert is_location_mismatch("Pune", "India") is False
    assert is_location_mismatch("Remote", "India") is False
    
    # Mismatch cases (should return True)
    assert is_location_mismatch("London, UK", "India") is True
    assert is_location_mismatch("New York, USA", "India") is True
    
    print("test_location_mismatch_filter passed.")

if __name__ == "__main__":
    # test_job_discovery_serper()
    # test_firecrawl_scraping()
    # test_resume_upload_integration()
    test_expired_jd_filter()
    test_location_mismatch_filter()
