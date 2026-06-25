import json
from evals import _call_llm_json, LLAMA_70B_MODELS
from config import GROQ_API_KEY

class MetadataParser:
    def __init__(self):
        self.api_key = GROQ_API_KEY

    def parse_poc_snippets(self, search_results, target_company_name: str, target_department: str):
        """Extract 1-2 current employee profiles from Serper search snippets.
        
        Args:
            search_results: Raw Serper API response
            target_company_name: The company we want employees FROM
            target_department: The team/department (e.g., "Product", "Engineering")
                              Used to filter out irrelevant departments
        """
        snippets = []
        for res in search_results.get("organic", []):
            snippets.append({
                "title": res.get("title"),
                "link": res.get("link"),
                "snippet": res.get("snippet")
            })

        dept_context = f'related to "{target_department}"' if target_department else "in any relevant team"

        prompt = f"""## System Persona
You are a High-Precision Entity Resolution Agent specializing in LinkedIn metadata. Your goal is to identify 1-2 CURRENT employees at the target company who could be relevant contacts for a job applicant.

## Context
- **Target Company:** {target_company_name}
- **Relevant Department:** {target_department or "Any (no specific team identified)"}
- **Input Data:** {json.dumps(snippets[:10], indent=2)}

## Extraction Rules (Apply in order)

### Rule 1: CURRENT Employment Verification (CRITICAL)
- The person MUST currently work at "{target_company_name}".
- REJECT if the snippet contains "Ex-", "Former", "Past", "Previously at", "Worked at" before "{target_company_name}".
- REJECT if "{target_company_name}" appears only in education, certifications, or project sections.
- Look for patterns like "Role at {target_company_name}" or "{target_company_name} | Role" — these indicate current employment.

### Rule 2: Entity Collision Check  
- Does the snippet indicate "{target_company_name}" as the **current employer**, or is the company name part of the person's name, a university, or another phrase?
- Example: "Fam Singh" is NOT an employee of "Fam Inc" — reject this collision.

### Rule 3: Department Relevance
- Prioritize people {dept_context}.
- REJECT profiles from clearly unrelated departments (e.g., if target is "Product", reject someone from "Marketing Analytics" or "Sales Operations").
- Hiring Managers, Team Leads, Recruiters, and Directors are always relevant regardless of department.

### Rule 4: LinkedIn URL Validation
- The link MUST be a direct profile URL containing "/in/" (not a company page, job listing, or post).

## Self-Critique (Internal check before output)
For each profile you select, verify:
1. "Is this person CURRENTLY at {target_company_name}, or is it a past role?"
2. "Is their role relevant to the {target_department or 'hiring'} context?"
3. "Is the LinkedIn URL a real profile link (/in/)?"

Return 1-2 profiles maximum. If no profiles pass all rules, return an empty array.

## Output Contract (JSON ONLY)
{{
  "profiles": [
    {{
      "name": "string",
      "linkedin_url": "string",
      "current_role": "string (their current title at the company)",
      "current_company": "{target_company_name}",
      "is_current_employee": true,
      "confidence_score": number (0.0-1.0)
    }}
  ]
}}
"""

        res = _call_llm_json(prompt, LLAMA_70B_MODELS, self.api_key, json_mode=True)
        if "error" in res:
            print(f"MetadataParser API Error: {res}")
            return {"profiles": []}
        
        # Post-processing: filter out any profiles the LLM marked as not current
        profiles = res.get("profiles", [])
        verified = [p for p in profiles if p.get("is_current_employee", False) is True]
        return {"profiles": verified}
