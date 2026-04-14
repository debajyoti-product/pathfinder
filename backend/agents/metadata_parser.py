import json
from config import GROQ_API_KEY
from services.usage_tracker import log_usage, is_over_limit
import httpx

class MetadataParser:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = "llama-3.3-70b-versatile"
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def parse_poc_snippets(self, search_results):
        """Extract exactly two profiles per job from Serper search snippets."""
        if is_over_limit("groq"):
            raise Exception("Groq API limit reached (60% threshold). Process paused.")

        snippets = []
        for res in search_results.get("organic", []):
            snippets.append({
                "title": res.get("title"),
                "link": res.get("link"),
                "snippet": res.get("snippet")
            })

        prompt = f"""
You are a high-precision data extraction agent. Analyze the following Google Search results metadata from LinkedIn and extract exactly TWO relevant profiles.

Extraction Task:
1. Identify the person's name from the result title (e.g., "Vidushi Saxena").
2. Extract the direct LinkedIn profile URL (/in/ link).
3. Identify their current role and company from the snippet (e.g., "Senior Product Manager | Bharti Airtel").
4. STRICT FILTER: Do NOT include profiles that indicate the person has left the company. Look for keywords like "Ex-", "Former", "Previous", "Past", or "At [Other Company]" in the title or snippet. If a profile says "Ex-Airbnb", it must be REJECTED if the target company is Airbnb.

Input Metadata (JSON):
{json.dumps(snippets[:10], indent=2)}

Output Requirements:
- Return exactly TWO profiles in the following JSON format.
- If fewer than two are relevant and CURRENTLY at the company, return as many as possible (but max 2).
- Be extremely accurate with name and role mapping.
- Only include people who are currently employed at the target company.

Output Schema:
{{
  "profiles": [
    {{
      "name": "string",
      "linkedinUrl": "string",
      "currentRole": "string"
    }}
  ]
}}
"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }

        with httpx.Client() as client:
            response = client.post(self.url, headers=headers, json=data, timeout=30.0)
            response.raise_for_status()
            log_usage("groq")
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
