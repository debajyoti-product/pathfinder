from dotenv import load_dotenv
load_dotenv('backend/.env')
import httpx, os, json
url = 'https://api.groq.com/openai/v1/chat/completions'
data = {
    'model': 'qwen/qwen3-32b',
    'messages': [{'role': 'user', 'content': 'Reply in JSON: {"test": "value"}'}],
    'response_format': {'type': 'json_object'}
}
res = httpx.post(
    url, 
    headers={'Authorization': 'Bearer ' + os.getenv('GROQ_API_KEY')}, 
    json=data
)
print(res.status_code)
print(res.text)
