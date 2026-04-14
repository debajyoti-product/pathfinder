import httpx
from config import HUNTER_API_KEY
from services.usage_tracker import log_usage, is_over_limit

class HunterClient:
    def __init__(self):
        self.api_key = HUNTER_API_KEY
        self.base_url = "https://api.hunter.io/v2"

    def find_email(self, first_name, last_name, domain):
        """Fetch email using Hunter.io API."""
        if not domain:
            return None
            
        if is_over_limit("hunter"):
            raise Exception("Hunter.io API limit reached (60% threshold). Process paused.")

        url = f"{self.base_url}/email-finder"
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": self.api_key
        }
        
        try:
            with httpx.Client() as client:
                response = client.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    log_usage("hunter")
                    return response.json().get("data", {}).get("email")
                return None
        except Exception:
            return None
