import sys
import os
import json

# Ensure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evals import _call_llama_json
from agents.resume_parser import ResumeParser

def test_raw_llama_parsing():
    """Test raw LLM parsing with a basic prompt (from legacy test.py)."""
    print("\n--- Testing Raw Llama Parsing (Legacy test.py) ---")
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

Resume Text:
Steve Jobs. I founded apple and have 30 years of experience. skills are visionary and hardware.
"""
    res = _call_llama_json(prompt)
    print(json.dumps(res, indent=2))

def test_resume_parser_agent():
    """Test the formal ResumeParser agent (from legacy test_parse.py)."""
    print("\n--- Testing ResumeParser Agent (Legacy test_parse.py) ---")
    parser = ResumeParser()
    resume_text = """
Debajyoti Biswas
iamdebajyoti850@gmail.com
9903777698

Product Manager with 2+ years of experience in building products to drive engagement & retention for 2mn+ users.

Skills: Prototyping, Prompt engineering, JIRA, Figma.

Experience
SaveIN (YC W22)
Product Manager
04/2025 - 09/2025

Cashkaro
Associate Product Manager
09/2023 - 05/2024
"""
    try:
        res = parser.parse(resume_text)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_raw_llama_parsing()
    test_resume_parser_agent()
