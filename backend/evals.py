import httpx
import json
import re
import time
from config import GROQ_API_KEY, CLOUDFLARE_API_KEY, CLOUDFLARE_ACCOUNT_ID
from services.usage_tracker import log_usage, is_over_limit

GPT_OSS_MODELS = [
    "openai/gpt-oss-120b"
]

# Backward-compatibility aliases
LLAMA_MODELS = GPT_OSS_MODELS
LLAMA_70B_MODELS = GPT_OSS_MODELS
QWEN_MODELS = GPT_OSS_MODELS

def _call_cloudflare_json(prompt: str, model: str) -> dict:
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_KEY:
        return {"error": "Cloudflare credentials missing. Please set CLOUDFLARE_ACCOUNT_ID in .env"}
        
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1/chat/completions"
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048
    }
    
    for attempt in range(2):
        with httpx.Client() as client:
            try:
                response = client.post(url, headers=headers, json=data, timeout=120.0)
                response.raise_for_status()
                result = response.json()
                
                # Cloudflare wraps result in 'result' sometimes for legacy, but v1/chat/completions follows OpenAI
                if "choices" in result:
                    content = result["choices"][0]["message"]["content"]
                elif "result" in result and "response" in result["result"]:
                    content = result["result"]["response"]
                else:
                    return {"error": "API returned invalid format", "raw": result}
                
                # Extract JSON
                json_match = re.search(r'```(?:json)?(.*?)```', content, flags=re.DOTALL | re.IGNORECASE)
                if json_match:
                    content = json_match.group(1).strip()
                else:
                    first_brace = content.find('{')
                    first_bracket = content.find('[')
                    start_idx = min(first_brace, first_bracket) if first_brace != -1 and first_bracket != -1 else max(first_brace, first_bracket)
                    if start_idx != -1:
                        end_idx = max(content.rfind('}'), content.rfind(']'))
                        if end_idx != -1:
                            content = content[start_idx:end_idx+1].strip()
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError as err:
                    import logging
                    logging.getLogger('pathfinder').error(f"JSON Parse Error: {err}. Raw content: {content}")
                    return {"error": "Failed to parse JSON", "raw": content}
                    
            except httpx.HTTPStatusError as e:
                if attempt < 1:
                    time.sleep(1)
                    continue
                return {"error": f"API Error (Cloudflare): {e.response.status_code} - {e.response.text}"}
            except Exception as e:
                if attempt < 1:
                    time.sleep(1)
                    continue
                return {"error": f"Request Error (Cloudflare): {str(e)}"}
                
    return {"error": "All models failed"}


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
                        if "TPD" in e.response.text or "tokens per day" in e.response.text:
                            break
                        wait_time = 6
                        try:
                            m = re.search(r'try again in (\d+(?:\.\d+)?)s', e.response.text)
                            if m:
                                wait_time = min(float(m.group(1)) + 1, 15)
                        except:
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

def _call_llama_text(prompt: str) -> str:
    if CLOUDFLARE_API_KEY:
        # call cloudflare and just return text
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "@cf/meta/llama-3.1-8b-instruct-fp8",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048
        }
        try:
            with httpx.Client() as client:
                res = client.post(url, headers=headers, json=data, timeout=120.0)
                res.raise_for_status()
                result = res.json()
                if "choices" in result:
                    return result["choices"][0]["message"]["content"].strip()
                elif "result" in result and "response" in result["result"]:
                    return result["result"]["response"].strip()
        except Exception as e:
            return f"Error: {e}"
    return ""

def _call_llama_json(prompt: str) -> dict:
    if CLOUDFLARE_API_KEY:
        return _call_cloudflare_json(prompt, "@cf/meta/llama-3.1-8b-instruct-fp8")
    return _call_llm_json(prompt, LLAMA_MODELS, GROQ_API_KEY, json_mode=True)

def _call_gpt_oss_json(prompt: str) -> dict:
    if GROQ_API_KEY:
        res = _call_llm_json(prompt, GPT_OSS_MODELS, GROQ_API_KEY, json_mode=True)
        if res and "error" not in res:
            return res
    if CLOUDFLARE_API_KEY:
        return _call_cloudflare_json(prompt, "@cf/meta/llama-3.1-8b-instruct-fp8")
    return res if GROQ_API_KEY else {"error": "No LLM provider available"}

# Backward-compatibility alias
_call_qwen_json = _call_gpt_oss_json
