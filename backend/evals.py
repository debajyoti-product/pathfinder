import httpx
import json
from config import QWEN_API_KEY

MODELS = [
    "qwen/qwen3-32b"
]

def _call_gemini_json(prompt: str) -> dict:
    import time

    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    last_error = None

    for model in MODELS:
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }

        for attempt in range(2): # Fail fast: Max 2 attempts
            with httpx.Client() as client:
                try:
                    response = client.post(url, headers=headers, json=data, timeout=30.0)
                    response.raise_for_status()
                    result = response.json()
                    
                    # Success — parse and return
                    try:
                        content = result["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        last_error = {"error": "API returned invalid format", "raw": result}
                        break  # Try next model
                    
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    elif content.startswith("```"):
                        content = content[3:-3].strip()
                    
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        last_error = {"error": "Failed to parse JSON", "raw": content}
                        break  # Try next model

                except httpx.ReadTimeout:
                    last_error = {"error": "DeepSeek API Timeout: The server took too long to respond."}
                    break # Fail fast on timeout, do not retry blindly
                except httpx.HTTPStatusError as e:
                    last_error = {"error": f"API Error ({model}): {e.response.status_code} - {e.response.text}"}
                    if e.response.status_code in [503, 500, 429] and attempt < 1:
                        time.sleep(1) # Minimal backoff
                        continue
                    break  # Try next model
                except Exception as e:
                    last_error = {"error": f"Request Error ({model}): {str(e)}"}
                    if attempt < 1:
                        time.sleep(1)
                        continue
                    break  # Try next model

    return last_error or {"error": "All models failed"}



def evaluate_job_match(jd_text: str, user_profile: dict) -> dict:
    prompt = f"""
You are an expert Recruitment Screener. Compare the User Profile to the provided Job Description (JD).

Decision Logic:
Experience Check: Does the JD explicitly require significantly more years than the user has? (e.g., JD asks for 8 years, User has 2).
Skill Check: Is there at least a 70% overlap in core technical skills?
Constraint: You MUST be extremely strict. If a role is labeled "Senior", "Staff", "Principal", or "Head" and the JD asks for 5-8+ years while the user has 0-3 years, return MATCH: FALSE. Do not be lenient. Bias towards FALSE if there is any doubt about the experience gap.

User Profile:
{json.dumps(user_profile)}

JD Snippet (First 3000 chars):
{jd_text[:3000]}

Return strictly a JSON object:
{{
  "match": boolean,
  "reason": "Short 1-sentence explanation",
  "confidence_score": 0.0-1.0
}}
    """
    res = _call_gemini_json(prompt)
    if "match" not in res:
        res["match"] = False
        res["confidence_score"] = 0.0
    return res

def extract_job_team_info(jd_text: str, user_profile: dict) -> dict:
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
- **Reject SEO Spam:** Many listings use "Remote" in the title but specify a "United States" location in the metadata (as seen in the provided image). These are US-Remote, not India-Remote. REJECT if the timezones or countries do not align.

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
    
    res = _call_gemini_json(prompt)
    if "isValidRange" not in res:
        res["isValidRange"] = False
    res.setdefault("required_years_extracted", "Unknown")
    res.setdefault("companyName", None)
    res.setdefault("teamName", None)
    return res


def evaluate_email_draft(news_snippet: str, drafted_email: str) -> dict:
    prompt = f"""
You are an expert Critic. Evaluate whether the drafted email effectively uses the company news snippet.
Rule: It must contain a specific Intent line that mentions the news naturally.

News Snippet:
{news_snippet}

Drafted Email:
{drafted_email}

Return strictly a JSON object:
{{
  "has_intent_line": boolean,
  "reason": "Short explanation"
}}
    """
    res = _call_gemini_json(prompt)
    if "has_intent_line" not in res:
        res["has_intent_line"] = False
    return res

def get_country(location: str) -> str:
    if not location:
        return ""
    prompt = f"Identify the country from this location string: '{location}'. Return strictly a JSON object: {{'country': 'string'}}"
    res = _call_gemini_json(prompt)
    if isinstance(res, dict) and "country" in res:
        return res["country"]
    return location # Fallback
