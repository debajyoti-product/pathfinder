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

def test_jd_location_prefilter():
    """Test the loose deterministic JD text location filter."""
    print("\n--- Testing JD Location Pre-filter ---")
    from main import is_jd_location_mismatch
    
    jd_remote = "We are a fully remote company looking for great people."
    jd_india = "Our office is located in Bengaluru, but we have people all over."
    jd_us = "Must be based in New York or San Francisco."
    
    assert is_jd_location_mismatch(jd_remote.lower(), "India") is False # Remote passes everything
    assert is_jd_location_mismatch(jd_india.lower(), "India") is False # Bengaluru -> India match
    assert is_jd_location_mismatch(jd_us.lower(), "India") is True # No mention of India/aliases/remote
    
    print("test_jd_location_prefilter passed.")

async def test_concurrent_cap_overshoot():
    """Test that concurrent evaluate_single_job calls don't exceed the jobs_found cap of 10."""
    print("\n--- Testing Concurrent Job Cap (Overshoot Prevention) ---")
    import main
    import asyncio
    import random
    
    # Mock the external calls to sleep slightly, forcing concurrency overlaps
    async def mock_fetch_and_clean_jd(url):
        await asyncio.sleep(random.uniform(0.01, 0.05))
        return "Fake JD India Product Manager"
        
    def mock_extract_job_team_info(jd, profile):
        return {"isValidRange": True, "required_years_extracted": "3", "companyName": "TestCo", "teamName": "Test"}
        
    def mock_find_poc_profiles(company, team):
        return []
        
    # Store originals
    orig_fetch = main.fetch_and_clean_jd
    orig_extract = main.extract_job_team_info
    orig_find_poc = main.find_poc_profiles
    
    # Apply mocks
    main.fetch_and_clean_jd = mock_fetch_and_clean_jd
    main.extract_job_team_info = mock_extract_job_team_info
    main.find_poc_profiles = mock_find_poc_profiles
    
    try:
        stats = {"jobs_found": 0, "pre_filtered": 0, "post_filtered": 0}
        queue = asyncio.Queue()
        sem = asyncio.Semaphore(3)
        profile_dict = {"job_title": "Product Manager", "location": "India", "actual_years_exp": 3.0}
        
        # Fire 15 concurrent jobs (cap is 10)
        tasks = []
        for i in range(15):
            tasks.append(asyncio.create_task(
                main.evaluate_single_job(f"http://example.com/{i}", "Test", f"Title {i}", queue, sem, profile_dict, 3.0, stats)
            ))
            
        await asyncio.gather(*tasks)
        
        print(f"Total jobs_found: {stats['jobs_found']}")
        assert stats["jobs_found"] == 10, f"Overshoot! Expected 10, got {stats['jobs_found']}"
        
        # Check queue yields exactly 10 valid job payloads (plus some status updates)
        valid_jobs = 0
        while not queue.empty():
            msg = queue.get_nowait()
            import json
            data = json.loads(msg.replace("data: ", "").strip())
            if "pocProfiles" in data:  # Only final job payloads have this
                valid_jobs += 1
                
        print(f"Total final payloads in queue: {valid_jobs}")
        assert valid_jobs == 10, f"Expected 10 job payloads in queue, got {valid_jobs}"
        print("test_concurrent_cap_overshoot passed.")
        
    finally:
        # Restore originals
        main.fetch_and_clean_jd = orig_fetch
        main.extract_job_team_info = orig_extract
        main.find_poc_profiles = orig_find_poc

if __name__ == "__main__":
    # test_job_discovery_serper()
    # test_firecrawl_scraping()
    # test_resume_upload_integration()
    test_expired_jd_filter()
    test_location_mismatch_filter()
    test_jd_location_prefilter()
    asyncio.run(test_concurrent_cap_overshoot())
