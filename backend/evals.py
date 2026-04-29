import httpx
import json
from config import GROQ_API_KEY

MODELS = [
    "llama-3.3-70b-versatile",
]

def _call_gemini_json(prompt: str) -> dict:
    import time

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    last_error = None

    for model in MODELS:
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
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
    prompt = f"""
You are an expert Recruitment Screener. Review the Job Description (JD) and the User Profile.

Goal:
1. Extract minimum years of experience required by JD.
2. Identify the specific team or department.
3. Validate if the required experience matches the user's actual_years_exp. 

STRICT VALIDATION RULES:
- If JD asks for 5+ years and user has < 3 years, return isValidRange: false.
- If JD asks for 8+ years and user has < 5 years, return isValidRange: false.
- If JD title contains "Senior", "Lead", "Staff", "Principal", "Director", "Head" and user has < 4 years of experience, return isValidRange: false.
- If JD is an "Intern" or "Associate" role and user has > 5 years, return isValidRange: false.
- If the JD does not mention years but the seniority level is clear from the title, apply the above rules.

User Profile:
{json.dumps(user_profile)}

JD Snippet (First 3000 chars):
{jd_text[:3000]}

Return strictly a JSON object:
{{
  "isValidRange": boolean,
  "teamName": "string or null",
  "requiredExperience": "string (e.g., '5-7 years')",
  "reason": "short explanation of the match/mismatch"
}}
    """
    res = _call_gemini_json(prompt)
    if "isValidRange" not in res:
        res["isValidRange"] = False
        res["teamName"] = None
        res["requiredExperience"] = "Unknown"
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
