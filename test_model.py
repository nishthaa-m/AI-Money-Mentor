from dotenv import load_dotenv; load_dotenv()
import os, requests

key = os.getenv('OPENROUTER_API_KEY')
models_to_try = [
    "google/gemini-flash-1.5-8b",
    "google/gemini-2.0-flash-001",
    "mistralai/mistral-7b-instruct",
    "qwen/qwen-2.5-7b-instruct",
]

for model in models_to_try:
    r = requests.post('https://openrouter.ai/api/v1/chat/completions',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={'model': model, 'messages': [{'role': 'user', 'content': 'reply with just: {"ok": true}'}], 'max_tokens': 20},
        timeout=10
    )
    data = r.json()
    if r.status_code == 200:
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"OK  {model}: {content[:50]}")
    else:
        err = data.get('error', {}).get('message', '')[:60]
        print(f"ERR {model}: {err}")
