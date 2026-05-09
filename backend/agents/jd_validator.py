from evals import _call_qwen_json


def extract_job_team_info(jd_text: str, user_profile: dict) -> dict:
    """
    Agent 3: Cynical Recruitment Gatekeeper (Qwen 3 32B)
    Applies 3 strict hard gates: Geography (India), Seniority, and Remote Policy.
    Returns isValidRange + reasoning_trace breakdown.
    """
    exp_summary = user_profile.get("experience_summary", [])
    if exp_summary and len(exp_summary) > 0:
        total_years = exp_summary[0].get("total_years_numeric", user_profile.get("actual_years_exp", 0))
        exp_range = exp_summary[0].get("experience_range", "Unknown")
    else:
        total_years = user_profile.get("actual_years_exp", 0)
        exp_range = "Unknown"

    remote_only = str(user_profile.get("remote_only", False)).lower()

    prompt = f"""## System Persona
You are a Cynical Recruitment Gatekeeper. Your goal is to DISQUALIFY jobs. Assume every job is a "False Positive" until it passes three high-integrity hardware gates: Geography, Seniority, and Remote-Policy.

## Input Data
- Candidate Experience: {exp_range} ({total_years} years)
- Remote Preference: {remote_only}
- JD Content: {jd_text[:1500]}

## THE THREE HARD GATES (Apply strictly)

### GATE 1: Geographic Integrity (India Only)
- **Metadata Check:** Look for location labels (e.g., "United States", "Philippines", "Manila"). 
- **SEO Trap Detection:** If the title says "Jobs in India" but the metadata or company HQ is listed elsewhere without an explicit "Remote India" option, REJECT.
- **Decision:** If the primary location is NOT India, `isValidRange: false`.

### GATE 2: Seniority & Title Mapping
- **Implicit Floor:** Titles like "Group Product Manager," "Staff," "Principal," or "Director" have a hard floor of 8+ years. 
- **The Match Rule:** If the candidate has < 8 years and the title is "Group PM" or "Staff," REJECT immediately.
- **Explicit Floor:** If the JD mentions "10+ years" or "12 years" and candidate is in the "1-3" or "3-5" bucket, REJECT.

### GATE 3: Remote Intent (If {remote_only} is True)
- **Strict Verification:** The JD must explicitly state "Remote," "WFH," or "Work from anywhere." 
- **Reject SEO Spam:** Many listings use "Remote" in the title but specify a "United States" location in the metadata. These are US-Remote, not India-Remote. REJECT if the timezones or countries do not align.

## Output Contract (JSON ONLY)
{{
  "isValidRange": boolean,
  "reasoning_trace": {{
    "location_gate": "Passed/Failed (Reason)",
    "experience_gate": "Passed/Failed (Reason)",
    "remote_gate": "Passed/Failed (Reason)"
  }},
  "confidence": number,
  "detected_location": "string",
  "required_years_extracted": "string"
}}"""

    res = _call_qwen_json(prompt)
    if not res or "error" in res:
        print(f"JD Validator Error: {res}")
        res = {"isValidRange": False, "reasoning_trace": {"location_gate": "Error", "experience_gate": "Error", "remote_gate": "Error"}}
    if "isValidRange" not in res:
        res["isValidRange"] = False
    res.setdefault("required_years_extracted", "Unknown")
    res.setdefault("companyName", None)
    res.setdefault("teamName", None)
    res.setdefault("reasoning_trace", {})
    return res
