import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import fetch_jd

def test_fetch_jd_firecrawl():
    print("--- Testing Firecrawl SDK Integration ---")
    
    # A real scrape URL that isn't LinkedIn (e.g. Greenhouse)
    test_url = "https://boards.greenhouse.io/discord/jobs/6131494?gh_src=db05a81e1us"
    
    # We will patch fetch_jina to ensure it is NOT called during a successful firecrawl
    with patch("main.fetch_jina") as mock_jina:
        mock_jina.return_value = "JINA FALLBACK"
        
        result = fetch_jd(test_url)
        
        # Jina shouldn't be called if firecrawl succeeds
        try:
            mock_jina.assert_not_called()
            print("[SUCCESS] fetch_jina fallback was NOT called")
        except AssertionError:
            print("[FAILURE] fetch_jina fallback WAS called")
            sys.exit(1)
            
        # Firecrawl result should be fairly substantial markdown
        assert len(result) > 200, f"Result too short: {len(result)} chars"
        assert "JINA FALLBACK" not in result, "Jina fallback string found in result"
        print(f"[SUCCESS] Scrape returned {len(result)} chars of markdown")
        print("test_fetch_jd_firecrawl passed.\n")

if __name__ == "__main__":
    test_fetch_jd_firecrawl()
