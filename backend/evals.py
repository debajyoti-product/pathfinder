import httpx
import json
import re
import time
from config import GROQ_API_KEY
from services.usage_tracker import log_usage, is_over_limit

LLAMA_MODELS = [
    "openai/gpt-oss-120b"
]

LLAMA_70B_MODELS = [
    "openai/gpt-oss-120b"
]

QWEN_MODELS = [
    "openai/gpt-oss-120b"
]

def _call_llm_json(prompt: str, models: list, api_key: str, json_mode: bool = True) -> dict:
    if is_over_limit("groq"):
        return {"error": "Groq API limit reached.", "limited": True}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    last_error = None
    for model in models:
        url = "https://api.groq.com/openai/v1/chat/completions"
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        if json_mode and "qwen" not in model.lower() and "deepseek" not in model.lower():
            data["response_format"] = {"type": "json_object"}
            
        for attempt in range(2):
            with httpx.Client() as client:
                try:
                    response = client.post(url, headers=headers, json=data, timeout=30.0)
                    response.raise_for_status()
                    log_usage("groq")
                    result = response.json()
                    try:
                        content = result["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        last_error = {"error": "API returned invalid format", "raw": result}
                        break
                    
                    # Strip <think> tags from reasoning models (GPT OSS 120B, DeepSeek-R1)
                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                    
                    # Robust JSON extraction
                    json_match = re.search(r'```(?:json)?(.*?)```', content, flags=re.DOTALL | re.IGNORECASE)
                    if json_match:
                        content = json_match.group(1).strip()
                    else:
                        # Fallback: extract substring from first '{' or '[' to last '}' or ']'
                        first_brace = content.find('{')
                        first_bracket = content.find('[')
                        start_idx = min(first_brace, first_bracket) if first_brace != -1 and first_bracket != -1 else max(first_brace, first_bracket)
                        if start_idx != -1:
                            end_idx = max(content.rfind('}'), content.rfind(']'))
                            if end_idx != -1:
                                content = content[start_idx:end_idx+1].strip()
                    
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        last_error = {"error": "Failed to parse JSON", "raw": content}
                        break
                except httpx.ReadTimeout:
                    last_error = {"error": f"API Timeout ({model})."}
                    break
                except httpx.HTTPStatusError as e:
                    last_error = {"error": f"API Error ({model}): {e.response.status_code} - {e.response.text}"}
                    if e.response.status_code in [503, 500, 429] and attempt < 1:
                        # Parse actual wait time from Groq error message
                        wait_time = 6  # default wait
                        try:
                            err_text = e.response.text
                            import re as _re
                            m = _re.search(r'try again in (\d+(?:\.\d+)?)s', err_text)
                            if m:
                                wait_time = min(float(m.group(1)) + 1, 15)
                        except Exception:
                            pass
                        time.sleep(wait_time)
                        continue
                    break
                except Exception as e:
                    last_error = {"error": f"Request Error ({model}): {str(e)}"}
                    if attempt < 1:
                        time.sleep(1)
                        continue
                    break

    return last_error or {"error": "All models failed"}

def _call_llama_json(prompt: str) -> dict:
    return _call_llm_json(prompt, LLAMA_MODELS, GROQ_API_KEY, json_mode=True)

def _call_qwen_json(prompt: str) -> dict:
    return _call_llm_json(prompt, QWEN_MODELS, GROQ_API_KEY, json_mode=True)
