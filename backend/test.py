from evals import _call_gemini_json

prompt = """
You are a precise Data Extraction Agent. Your goal is to convert a resume into a structured search profile.

Output Schema (JSON):
{
  "job_title": "Primary role title",
  "skills": ["skill1", "skill2"],
  "actual_years_exp": integer,
  "search_range": ["range1"],
  "industry": "e.g. Fintech, SaaS"
}

logic for range:
calculate years of experience by the dates mentioned in each experience. for profiles with no experience, keep range as ["0-1 years"].
If exp = 2, range = ["1-3 years"].

Resume Text:
Steve Jobs. I founded apple and have 30 years of experience. skills are visionary and hardware.
"""

print(_call_gemini_json(prompt))
