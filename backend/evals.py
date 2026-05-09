import httpx
import json
from config import QWEN_API_KEY, GROQ_API_KEY

LLAMA_MODELS = [
    "llama-3.1-8b-instant",
    "llama3-8b-8192"
]

QWEN_MODELS = [
    "qwen/qwen3-32b"
]

def _call_llama_json(prompt: str) -> dict:
    import time
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    last_error = None
    for model in LLAMA_MODELS:
        url = "https://api.groq.com/openai/v1/chat/completions"
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        for attempt in range(2):
            with httpx.Client() as client:
                try:
                    response = client.post(url, headers=headers, json=data, timeout=30.0)
                    response.raise_for_status()
                    result = response.json()
                    try:
                        content = result["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        last_error = {"error": "API returned invalid format", "raw": result}
                        break
                    
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    elif content.startswith("```"):
                        content = content[3:-3].strip()
                    
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        last_error = {"error": "Failed to parse JSON", "raw": content}
                        break
                except httpx.ReadTimeout:
                    last_error = {"error": "Groq API Timeout."}
                    break
                except httpx.HTTPStatusError as e:
                    last_error = {"error": f"API Error ({model}): {e.response.status_code} - {e.response.text}"}
                    if e.response.status_code in [503, 500, 429] and attempt < 1:
                        time.sleep(1)
                        continue
                    break

def _call_qwen_json(prompt: str) -> dict:
    import time
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    last_error = None
    for model in QWEN_MODELS:
        url = "https://api.groq.com/openai/v1/chat/completions"
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        for attempt in range(2):
            with httpx.Client() as client:
                try:
                    response = client.post(url, headers=headers, json=data, timeout=30.0)
                    response.raise_for_status()
                    result = response.json()
                    try:
                        content = result["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        last_error = {"error": "API returned invalid format", "raw": result}
                        break
                    
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    elif content.startswith("```"):
                        content = content[3:-3].strip()
                    
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        last_error = {"error": "Failed to parse JSON", "raw": content}
                        break
                except httpx.ReadTimeout:
                    last_error = {"error": "Qwen API Timeout."}
                    break
                except httpx.HTTPStatusError as e:
                    last_error = {"error": f"API Error ({model}): {e.response.status_code} - {e.response.text}"}
                    if e.response.status_code in [503, 500, 429] and attempt < 1:
                        time.sleep(1)
                        continue
                    break
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
    res = _call_llama_json(prompt)
    if "match" not in res:
        res["match"] = False
        res["confidence_score"] = 0.0
    return res


def get_country(location: str) -> str:
    if not location:
        return ""
    prompt = f"Identify the country from this location string: '{location}'. Return strictly a JSON object: {{'country': 'string'}}"
    res = _call_llama_json(prompt)
    if isinstance(res, dict) and "country" in res:
        return res["country"]
    return location # Fallback
