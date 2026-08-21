import os
import requests
from dotenv import load_dotenv

load_dotenv('backend/.env')
api_key = os.getenv('NIM_API_KEY') or os.getenv('LLM_API_KEY_NIM')
print('API Key exists:', bool(api_key))

payload = {
    'model': 'deepseek-ai/deepseek-v4-flash-0731',
    'messages': [{'role': 'user', 'content': 'Respond with JSON: {"test": 1}'}],
    'max_tokens': 100,
    "chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}
}

res = requests.post(
    'https://integrate.api.nvidia.com/v1/chat/completions',
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    json=payload
)
print(res.status_code)
print(res.text[:500])
