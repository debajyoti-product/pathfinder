import json
from config import GROQ_API_KEY
from services.usage_tracker import log_usage, is_over_limit
import httpx

class MetadataParser:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = "llama-3.3-70b-versatile"
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def parse_poc_snippets(self, search_results, target_company_name: str, target_role_type: str):
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

        prompt = f"""## System Persona
You are a High-Precision Entity Resolution Agent specializing in LinkedIn metadata. Your goal is to identify current employees (Peers) at a target company while strictly filtering out "Ex-employees" and "Name-Company collisions."

## Context
- **Target Company:** {target_company_name}
- **Target Role Type:** {target_role_type}
- **Input Data:** {json.dumps(snippets[:10], indent=2)}

## Extraction Logic & Hard Gates
1. **Entity Collision Check:** Does the snippet indicate "{target_company_name}" as the **Employer**, or is it just part of a name/other phrase? (e.g., "Fam Smith" vs "Product at Fam"). If it's not the Employer, REJECT.
2. **Current Employment Verification:** - Search for "Ex-", "Former", "Past", "Worked at". If these prefixes are attached to the target company, REJECT.
   - Look for separators like "|" or "-" in titles. The company following the role MUST match the target company.
3. **Peer Match:** Prioritize profiles where the role contains keywords related to "{target_role_type}".

## Self-Critique Loop (Internal Monologue)
Before finalizing the JSON, ask yourself:
- "Is 'Vidushi Saxena' actually at '{target_company_name}', or does the snippet just mention her past experience there?"
- "Did I pick this person because their name contains the company string? (e.g., 'Fam' in name vs company)."
- "Is the LinkedIn URL a direct profile link (/in/) and not a company page?"

return 2 profiles per job.

## Output Contract (JSON ONLY)
{{
  "profiles": [
    {{
      "name": "string",
      "linkedin_url": "string",
      "current_role": "string",
      "current_company": "string",
      "is_current_employee": true,
      "confidence_score": number
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

        try:
            with httpx.Client() as client:
                response = client.post(self.url, headers=headers, json=data, timeout=30.0)
                response.raise_for_status()
                log_usage("groq")
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except (httpx.HTTPStatusError, httpx.ReadTimeout) as e:
            print(f"MetadataParser API Error: {e}")
            return {"profiles": []}
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"MetadataParser Parse Error: {e}")
            return {"profiles": []}
