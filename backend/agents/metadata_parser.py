import json
from evals import _call_llm_json, LLAMA_70B_MODELS
from config import GROQ_API_KEY

class MetadataParser:
    def __init__(self):
        self.api_key = GROQ_API_KEY

    def parse_poc_snippets(self, search_results, target_company_name: str, target_role_type: str):
        """Extract exactly two profiles per job from Serper search snippets."""
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

        res = _call_llm_json(prompt, LLAMA_70B_MODELS, self.api_key, json_mode=True)
        if "error" in res:
            print(f"MetadataParser API Error: {res}")
            return {"profiles": []}
        return res
