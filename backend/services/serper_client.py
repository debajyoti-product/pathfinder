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

    def search(self, query, search_type="search", tbs=None):
        """General purpose search method."""
        payload = {"q": query}
        if tbs:
            payload["tbs"] = tbs
        return self._call_api(search_type, payload)

    def search_jobs(self, query):
        """Find relevant job board links."""
        payload = {"q": query}
        return self._call_api("search", payload)

    def search_linkedin_pocs(self, company, team=None):
        """Search for CURRENT employees at the company in the relevant department.
        
        Strategy:
        - Uses "current" keyword to bias Google towards active employees
        - Uses team/department to stay department-relevant
        - Leadership keywords find hiring managers, not individual contributors
        - Does NOT include job title — hiring managers have different titles
        """
        team_str = f'"{team}"' if team else ""
        # The "current" keyword helps Google prioritize active employees
        # over people who list the company as a past employer
        query = f'site:linkedin.com/in/ current "{company}" {team_str} ("Manager" OR "Lead" OR "Head" OR "Recruiter" OR "Director")'
        payload = {"q": query}
        return self._call_api("search", payload)
