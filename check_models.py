import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ Error: API Key not found in .env")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        print("✅ SUCCESS! Here are the models your key can use:\n")
        data = response.json()
        for model in data.get('models', []):
            # We only care about models that can generate content (chat)
            if "generateContent" in model.get('supportedGenerationMethods', []):
                print(f"👉 {model['name']}")
    else:
        print(f"❌ Error listing models: {response.text}")