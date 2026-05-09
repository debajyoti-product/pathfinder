import asyncio
from evals import _call_llama_json
import json

resume_text = """
Debajyoti Biswas
iamdebajyoti850@gmail.com
9903777698

Product Manager with 2+ years of experience in building products to drive engagement & retention for 2mn+ users & additionally, yielding INR 60L+ in incremental growth

Skills:
Product: Prototyping, Prompt engineering, Market research, API integration, Documentation, Data analysis, Funnel optimization
Tools: JIRA, Figma, Lovable, Replit, Postman, DBeaver, Claude, GPT, Firebase, Google analytics, Gupshup

Experience
SaveIN (YC W22)
Product Manager
04/2025 - 09/2025

Cashkaro
Associate Product Manager
09/2023 - 05/2024

Guide
Founder
12/2022 - 09/2023

Swift
Associate Product Manager
04/2022 - 11/2022

Digit Insurance
Analyst
01/2020 - 04/2021
"""

prompt = f"""Persona: You are a high-precision Resume Data Analysis Agent for the Pathfinder AI Suite. Your goal is to transform unstructured resume data extracted from pypdf into a normalized JSON contract that serves as the "Single Source of Truth" for downstream job validation agents.

Task
1. **Raw Extraction:** Extract all roles, skills, and contact metadata.
2. **Role Segregation:** Identify distinct career tracks (e.g., "Product Manager", "Software Engineer") 
3. **Experience Normalization:** For each career track, calculate the total duration in years and map it to a specific range bucket.

Normalization Rules (Strict)
- **Role Type:** Group similar titles into logical categories (e.g., "Senior PM" and "Associate PM" both belong to the "Product Manager" category).
- **Date Calculation:** Perform the math between start and end dates. Use current date for "Present" calculations. Calculate "total_years_numeric" from months (e.g., 9 months + 8 months = 1.41 or 1.5 years).
- **Experience Range Buckets:** You MUST map every `role_type` to exactly one of these: `0-1 year`, `1-3 years`, `3-5 years`, `5-8 years`, `8-12 years`, `12+ years`.
- **Skills:** Extract as individual keywords from dedicated Skills/Tools section.

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
{resume_text}"""

res = _call_llama_json(prompt)
print(json.dumps(res, indent=2))
