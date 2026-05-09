import sys, os
sys.path.insert(0, '.')
os.chdir(r'c:\Users\Debajyoti\.antigravity\Pathfinder\pathfinder-ai-suite\backend')

from config import SERPER_API_KEY, FIRECRAWL_API_KEY
print(f'SERPER_API_KEY: {bool(SERPER_API_KEY)}')
print(f'FIRECRAWL_API_KEY: {bool(FIRECRAWL_API_KEY)}')

import httpx, json

url = 'https://google.serper.dev/search'
headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}

# Test 1: LinkedIn
payload = {'q': 'site:linkedin.com/jobs/view "Product Manager" "India"'}
with httpx.Client() as client:
    res = client.post(url, headers=headers, json=payload, timeout=30)
    data = res.json()
    organic = data.get('organic', [])
    print(f'\nLinkedIn search results: {len(organic)}')
    for item in organic[:3]:
        print(f'  - {item.get("link", "N/A")[:100]}')

# Test 2: Naukri
payload2 = {'q': 'site:naukri.com "Product Manager" "India"'}
with httpx.Client() as client:
    res2 = client.post(url, headers=headers, json=payload2, timeout=30)
    data2 = res2.json()
    organic2 = data2.get('organic', [])
    print(f'\nNaukri search results: {len(organic2)}')
    for item in organic2[:3]:
        print(f'  - {item.get("link", "N/A")[:100]}')

# Test 3: Firecrawl scrape a Naukri URL
if organic2:
    test_url = organic2[0].get('link')
    if test_url:
        print(f'\nTesting Firecrawl scrape on: {test_url}')
        from firecrawl import V1FirecrawlApp
        fc = V1FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        try:
            result = fc.scrape_url(test_url, formats=['markdown'], only_main_content=True, timeout=30000)
            md = result.markdown or ''
            print(f'Scrape result length: {len(md)}')
            print(f'First 300 chars: {md[:300]}')
        except Exception as e:
            print(f'Scrape error: {e}')
