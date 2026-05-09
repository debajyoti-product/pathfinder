import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser as date_parser
from evals import _call_llama_json


class ResumeParser:
    """
    Agent 1: Resume Data Extraction Agent (Llama 3.1 8B via Groq)
    Extracts roles, skills, and dates from raw PDF text.
    Python Date Math Engine overrides all LLM duration calculations.
    """

    def parse(self, text: str) -> dict:
        prompt = f"""Persona: You are a high-precision Resume Data Analysis Agent for the Pathfinder AI Suite. Your goal is to transform unstructured resume data extracted from pypdf into a normalized JSON contract that serves as the "Single Source of Truth" for downstream job validation agents.

Task
1. **Raw Extraction:** Extract all roles, skills, and contact metadata.
2. **Role Segregation:** Identify distinct career tracks (e.g., "Product Manager", "Software Engineer") 
3. **Experience Normalization:** For each career track, calculate the total duration in years and map it to a specific range bucket.

Normalization Rules (Strict)
- **Role Type:** Group similar titles into logical categories (e.g., "Senior PM" and "Associate PM" both belong to the "Product Manager" category).
- **Date Extraction:** Focus entirely on extracting the precise `start_date` and `end_date` (MM/YYYY) from the "Experience" section. A Python backend script will override your math, so just fetch the dates accurately!
- **Experience Range Buckets:** Give your best estimate. The backend will override this too.
- **Skills:** Extract as individual keywords from dedicated Skills/Tools section.

Critical Calculation Constraints
1. **Source Lockdown:** Extract experience dates ONLY from the "Experience" section. STRICTLY IGNORE any years mentioned in the "Summary," "About Me," or "Professional Profile" sections.
2. **No Duplicate Extraction:** Do not list the same company/role combination twice.
3. **SHORT REMINDER:** You do not need to do complex date math. Just accurately extract the `roles` array with start/end dates. The Python backend will calculate the exact duration and aggregate the `experience_summary`.

Constraints
- Format: Return ONLY valid JSON. No conversational filler.
- Accuracy: Do not hallucinate skills not present in the text.
- Location: Do NOT extract location.

If a field is not present, return NULL only then.

Output Contract (JSON)
{{
  "experience_summary": [
    {{
      "role_type": "string (e.g., 'Product Manager', 'Analyst')",
      "total_years_numeric": number,
      "experience_range": "string (one of: 0-1 year, 1-3 years, 3-5 years, 5-8 years, 8-12 years, 12+ years)"
    }}
  ],
  "skills": ["string", "string"],
  "industry": "string (e.g., Fintech, Logistics)",
  "roles": [
    {{
      "title": "string",
      "start_date": "MM/YYYY",
      "end_date": "MM/YYYY or present"
    }}
  ]
}}

Resume:
{text[:4000]}"""

        result = _call_llama_json(prompt)
        if "error" in result:
            raise ValueError(f"LLM Error: {result['error']}")

        # ── Python Date Math Override ───────────────────────────────────────
        # Never trust LLM arithmetic. We recalculate all durations here.
        def parse_date(d_str):
            if not d_str or str(d_str).lower() in ["present", "current", "now", "null"]:
                return datetime.datetime.now()
            d_str = str(d_str).strip().lower().replace("present", "").replace("current", "")
            if not d_str:
                return datetime.datetime.now()
            try:
                return date_parser.parse(d_str, default=datetime.datetime(2000, 1, 1))
            except:
                return datetime.datetime.now()

        summary_map = {}
        for role in result.get("roles", []):
            start = parse_date(role.get("start_date"))
            end = parse_date(role.get("end_date"))
            diff = relativedelta(end, start)
            years = diff.years + (diff.months / 12.0)
            if years < 0:
                years = 0.0
            if years == 0 and (end.month != start.month or end.year != start.year):
                years = 1 / 12.0

            title = role.get("title", "Unknown Role")
            if title in summary_map:
                summary_map[title] += years
            else:
                summary_map[title] = years

        new_summary = []
        for title, y in summary_map.items():
            new_summary.append({
                "role_type": title,
                "total_years_numeric": round(y, 2),
                "experience_range": "0-1 years"  # Frontend recalculates exact bucket
            })

        result["experience_summary"] = new_summary
        return result
