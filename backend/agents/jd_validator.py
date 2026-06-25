from evals import _call_qwen_json


def extract_job_team_info(jd_text: str, user_profile: dict) -> dict:
    """
    Agent 3: Cynical Recruitment Gatekeeper (Qwen 3 32B)
    Applies 3 strict hard gates: Geography, Seniority/Experience, and Remote Policy.
    Also extracts companyName from the JD for downstream POC search.
    Returns isValidRange + reasoning_trace breakdown + companyName.
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
You are a Cynical Recruitment Gatekeeper. Your goal is to DISQUALIFY jobs that don't match the candidate. Assume every job is a "False Positive" until it passes three high-integrity gates.

## Candidate Profile
- Target Role: {job_title}
- Total Experience: {total_years} years (range: {exp_range})
- Key Skills: {skills_str}
- Preferred Location: {user_location}
- Remote Only: {remote_only}

## JD Content
{jd_text[:3000]}

## THE THREE HARD GATES

### GATE 1: Experience Match (HIGHEST PRIORITY)
This is the most important gate. You must extract the EXACT experience requirement from the JD and compare it to the candidate's {total_years} years.
- **Extract Required Years:** Find phrases like "X+ years", "X-Y years of experience", "minimum X years". Extract the number.
- **Hard Reject Rules:**
  - If JD requires 7+ years and candidate has {total_years} years → REJECT
  - If JD title contains "Senior" / "Lead" / "Staff" / "Principal" / "Director" / "Head" / "Group" AND requires 6+ years AND candidate has < 5 years → REJECT
  - If JD requires 0-2 years and candidate has {total_years} years → This is fine (overqualified is OK)
- **Acceptable Match Window:** The candidate's {total_years} years must fall within ±2 years of the JD's stated requirement. e.g., JD asks "3-5 years", candidate with {total_years} years is acceptable if {total_years} >= 1 AND {total_years} <= 7.
- If NO experience requirement is stated, PASS this gate but note it.

### GATE 2: Geographic Integrity ({user_location})
- If the JD's primary location is clearly NOT {user_location} (e.g., "United States only", "Manila", "London"), REJECT.
- SEO traps: title says "{user_location}" but metadata says another country → REJECT.
- If location is ambiguous or "Remote" without country restriction → PASS.

### GATE 3: Remote Policy (Only if remote_only = true)
- The JD must explicitly state "Remote", "WFH", or "Work from anywhere" for {user_location}.
- If remote_only is false, auto-PASS this gate.

## Extraction Tasks (Required regardless of pass/fail)
Extract these from the JD text:
1. **companyName**: The hiring company's name as written in the JD. Look for "About [Company]", "at [Company]", header text, or footer.
2. **teamName**: The team or department (e.g., "Growth", "Platform", "Engineering"). Return null if not found.
3. **required_years_extracted**: The exact experience requirement string from the JD (e.g., "3-5 years", "5+ years"). Return "Not specified" if not found.

## Output Contract (JSON ONLY)
{{
  "isValidRange": boolean,
  "reasoning_trace": {{
    "experience_gate": "Passed/Failed — JD asks [X], candidate has {total_years} yrs. [Reason]",
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
