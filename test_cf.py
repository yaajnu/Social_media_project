import requests
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("CLOUDFARE_API_KEY", "")
print(f"Key length: {len(api_key)}, starts with: {api_key[:8]}...")

url = "https://llm-chat-app-template.yaajnusubramanian.workers.dev/api/generate"
headers = {
    "Content-Type": "application/json",
    "Accept": "image/png,image/*,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin": "https://llm-chat-app-template.yaajnusubramanian.workers.dev",
    "Referer": "https://llm-chat-app-template.yaajnusubramanian.workers.dev/",
    "X-API-Key": api_key,
}

resp = requests.post(
    url, headers=headers, json={"prompt": "a red apple on a white table"}, timeout=60
)
print("Status:", resp.status_code)
print("Content-Type:", resp.headers.get("Content-Type"))
print("Content length:", len(resp.content))
if not resp.ok:
    print("Error body:", resp.text[:500])
else:
    with open("test_output.png", "wb") as f:
        f.write(resp.content)
    print("Saved to test_output.png")
