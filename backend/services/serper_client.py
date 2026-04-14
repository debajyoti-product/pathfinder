import httpx
from config import SERPER_API_KEY
from services.usage_tracker import log_usage, is_over_limit

class SerperClient:
    def __init__(self):
        self.api_key = SERPER_API_KEY
        self.base_url = "https://google.serper.dev"

    def _call_api(self, endpoint, payload):
        if is_over_limit("serper"):
            raise Exception("Serper API limit reached (60% threshold). Process paused.")
            
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        url = f"{self.base_url}/{endpoint}"
        
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            log_usage("serper")
            return response.json()

    def search_jobs(self, query):
        """Find relevant job board links."""
        payload = {"q": query}
        return self._call_api("search", payload)

    def find_company_domain(self, company_name):
        """Search for the official company domain (supporting .com, .ai, .in, etc.)."""
        query = f'official website of "{company_name}"'
        payload = {"q": query}
        res = self._call_api("search", payload)
        
        organic = res.get("organic", [])
        if not organic:
            return None
            
        # Extract domain from the first result link
        link = organic[0].get("link", "")
        if link:
            from urllib.parse import urlparse
            domain = urlparse(link).netloc
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        return None

    def search_linkedin_pocs(self, company, team, job_title):
        """Perform site-restricted search for LinkedIn POCs."""
        team_str = f'"{team}"' if team else ""
        query = f'site:linkedin.com/in/ "{company}" {team_str} "{job_title}"'
        payload = {"q": query}
        return self._call_api("search", payload)
