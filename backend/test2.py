import sys
sys.path.insert(0, '.')
from evals import _call_gemini_json

prompt = """
You are a precise Data Extraction Agent. Your goal is to convert a resume into a structured search profile.

Output Schema (JSON):
{
  "job_title": "Primary role title",
  "skills": ["skill1", "skill2"],
  "actual_years_exp": 3,
  "search_range": ["range1"],
  "industry": "e.g. Fintech, SaaS"
}

Resume Text:
Software Engineer at Google. 5 years experience in Python and C++.
"""
res = _call_gemini_json(prompt)
print(res)
