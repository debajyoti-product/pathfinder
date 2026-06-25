import httpx
import json
import re
import time
from config import QWEN_API_KEY, GROQ_API_KEY
from services.usage_tracker import log_usage, is_over_limit

LLAMA_MODELS = [
    "llama-3.1-8b-instant",
    "llama3-8b-8192"
]

LLAMA_70B_MODELS = [
    "llama-3.3-70b-versatile"
]

QWEN_MODELS = [
    "qwen/qwen3-32b"
]

def _call_llm_json(prompt: str, models: list, api_key: str, json_mode: bool = True) -> dict:
    if is_over_limit("groq"):
        return {"error": "Groq API limit reached (60% threshold). Process paused."}

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
        if json_mode:
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
                    
                    # Strip <think> tags from reasoning models (Qwen, DeepSeek-R1)
                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                    
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
                    last_error = {"error": f"API Timeout ({model})."}
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
                    break

    return last_error or {"error": "All models failed"}

def _call_llama_json(prompt: str) -> dict:
    return _call_llm_json(prompt, LLAMA_MODELS, GROQ_API_KEY, json_mode=True)

def _call_qwen_json(prompt: str) -> dict:
    return _call_llm_json(prompt, QWEN_MODELS, QWEN_API_KEY, json_mode=False)
