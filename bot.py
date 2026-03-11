import os
import re
import joblib
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from features import extract_features

# 1. LOAD SECRETS
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 2. SETUP FLASK
app = Flask(__name__)

# 3. LOAD ML MODEL
try:
    model_ml = joblib.load('phish_model.pkl')
    print("✅ ML Model Loaded")
except:
    print("❌ Critical Error: 'phish_model.pkl' not found.")

# VIP WHITELIST
WHITELIST = ['google.com', 'www.google.com', 'youtube.com', 'amazon.com', 'wikipedia.org']


def get_ai_explanation(url, risk_score):
    """
    Directly emails Google's API using the stable model alias.
    Includes fallback logic for when the AI service is busy.
    """
    if not API_KEY: return "Error: API Key missing."

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"

    prompt_text = (
        f"I am a security bot. Analyze this URL: {url}. "
        f"My ML model gives it a risk score of {risk_score}/100. "
        "Explain in 1 short sentence why it is safe or dangerous."
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    try:
        # Added a 5-second timeout to prevent the bot from hanging
        response = requests.post(api_url, json=payload, timeout=5)
        data = response.json()

        # SUCCESS: Return AI-generated text
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # ERROR HANDLING: If AI is busy or quota exceeded
        if "error" in data:
            error_msg = data['error']['message']
            print(f"⚠️ AI Error: {error_msg}")

            # FALLBACK LOGIC: Provide a useful response even if AI fails
            if risk_score > 50:
                return "AI is currently busy, but the ML scan flags this as a high-risk link. Proceed with extreme caution."
            elif risk_score > 30:
                return "AI is currently busy, but the ML scan suggests some suspicious patterns in this URL."
            else:
                return "AI is busy, but the ML scan indicates this link structure is likely safe."

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return "AI analysis currently unavailable. ML scan suggests staying alert."


@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # FIND LINK
    url_match = re.search(r'((http|https)://)?(www\.)?[\w-]+\.\w+(/[\w\- ./?%&=]*)?', incoming_msg)

    if url_match:
        url = url_match.group(0)
        if not url.startswith(('http://', 'https://')): url = f'https://{url}'

        # CHECK WHITELIST
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")
        if domain in WHITELIST:
            msg.body(f"✅ *OFFICIALLY VERIFIED*\n🔗 {url}\n\n🤖 AI: Trusted Website.")
            return str(resp)

        # RUN SCAN
        try:
            features = extract_features(url)
            ml_prob = model_ml.predict_proba([features])[0][1]
            risk_percent = int(ml_prob * 100)

            # Call AI
            ai_text = get_ai_explanation(url, risk_percent)

            if risk_percent > 50:
                verdict = "🚨 *DANGEROUS*"
            elif risk_percent > 30:
                verdict = "⚠️ *SUSPICIOUS*"
            else:
                verdict = "✅ *SAFE*"

            msg.body(f"{verdict}\n🔗 {url}\n📊 Risk: {risk_percent}/100\n\n🤖 AI Insight: {ai_text}")

        except Exception as e:
            msg.body(f"⚠️ Error: {str(e)}")

    else:
        msg.body("🛡️ Bharat Phish-Guard\nSend me a link to scan!")

    return str(resp)


if __name__ == "__main__":
    app.run(port=5000)