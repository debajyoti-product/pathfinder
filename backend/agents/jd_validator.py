from evals import _call_qwen_json


def extract_job_team_info(jd_text: str, user_profile: dict) -> dict:
    """
    Agent 3: Cynical Recruitment Gatekeeper (Qwen 3 32B)
    Applies 3 strict hard gates: Experience Match (P0), Geography, and Remote Policy.
    Also extracts companyName from the JD for downstream POC search.
    """
    exp_summary = user_profile.get("experience_summary", [])
    if exp_summary and len(exp_summary) > 0:
        total_years = exp_summary[0].get("total_years_numeric", user_profile.get("actual_years_exp", 0))
        exp_range = exp_summary[0].get("experience_range", "Unknown")
    else:
        total_years = user_profile.get("actual_years_exp", 0)
        search_range = user_profile.get("search_range", ["Unknown"])
        exp_range = search_range[0] if search_range else "Unknown"

    remote_only = str(user_profile.get("remote_only", False)).lower()

    user_location = user_profile.get("location", "India")
    if not user_location:
        user_location = "India"

    user_skills = user_profile.get("skills", [])
    skills_str = ", ".join(user_skills[:15]) if user_skills else "Not provided"

    job_title = user_profile.get("job_title", "Unknown")

    prompt = f"""## System Persona
You are a Cynical Recruitment Gatekeeper. Your default answer is REJECT. Only pass a job if it CLEARLY matches the candidate's experience level. When in doubt, REJECT.

## Candidate Profile
- Target Role: {job_title}
- Total Experience: {total_years} years (bucket: {exp_range})
- Key Skills: {skills_str}
- Preferred Location: {user_location}
- Remote Only: {remote_only}

## JD Content
{jd_text[:3000]}

## THE THREE HARD GATES (Strictest first)

### GATE 1: Experience Match (HIGHEST PRIORITY — be extremely strict)
Extract the EXACT experience requirement from the JD. Then apply these rules:

**HARD REJECT if ANY of these are true:**
- The JD title contains "Senior", "Sr.", "Lead", "Staff", "Principal", "Director", "Head", "VP", "AVP", "Group PM", "Distinguished", "Architect", or "Specialist" AND the candidate has less than 5 years → REJECT
- The JD states a minimum of X years AND X > {total_years} + 1 → REJECT (e.g., JD asks "4+ years" and candidate has {total_years} years = REJECT if {total_years} < 3)
- The JD states a range like "X-Y years" AND X > {total_years} + 1 → REJECT

**PASS only if:**
- The JD's minimum requirement is ≤ {total_years} + 1 year (small stretch is OK)
- OR the JD does not state any experience requirement AND the title does not contain senior keywords

### GATE 2: Geographic Integrity ({user_location})
- If the JD's primary location is clearly NOT {user_location}, REJECT.
- SEO traps: title says "{user_location}" but body/metadata says another country → REJECT.
- Ambiguous or "Remote" without country restriction → PASS.

### GATE 3: Remote Policy (Only applies if remote_only = true)
- JD must explicitly state "Remote", "WFH", or "Work from anywhere" for {user_location}.
- If remote_only is false, auto-PASS.

## Extraction Tasks (ALWAYS extract, even if rejecting)
1. **companyName**: The hiring company's name from the JD text. Look for "About [Company]", "at [Company]", header, footer.
2. **teamName**: The team/department (e.g., "Growth", "Platform"). null if not found.
3. **required_years_extracted**: The exact experience requirement string (e.g., "3-5 years", "5+ years", "Not specified").

## Output Contract (JSON ONLY — no other text)
{{
  "isValidRange": boolean,
  "reasoning_trace": {{
    "experience_gate": "Passed/Failed — JD requires [X], candidate has {total_years} yrs. [Reason]",
    "location_gate": "Passed/Failed — [Reason]",
    "remote_gate": "Passed/Failed — [Reason]"
  }},
  "confidence": number (0.0-1.0),
  "companyName": "string or null",
  "teamName": "string or null",
  "detected_location": "string",
  "required_years_extracted": "string"
}}"""

    res = _call_qwen_json(prompt)
    if not res or "error" in res:
        print(f"JD Validator Error: {res}")
        res = {"isValidRange": False, "reasoning_trace": {"experience_gate": "Error", "location_gate": "Error", "remote_gate": "Error"}}
    if "isValidRange" not in res:
        res["isValidRange"] = False
    res.setdefault("required_years_extracted", "Unknown")
    res.setdefault("companyName", None)
    res.setdefault("teamName", None)
    res.setdefault("reasoning_trace", {})
    return res
