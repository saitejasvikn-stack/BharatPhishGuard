import streamlit as st
import joblib
import sqlite3
import requests
import time
from google.genai import errors
from google import genai
from features import extract_features


# 1. DATABASE SETUP
def init_db():
    conn = sqlite3.connect('blacklist.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS scams (url TEXT PRIMARY KEY, risk_score REAL)')
    conn.commit()
    conn.close()


def add_to_blacklist(url, score):
    try:
        conn = sqlite3.connect('blacklist.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO scams VALUES (?, ?)', (url, score))
        conn.commit()
        conn.close()
    except:
        pass


def is_blacklisted(url):
    conn = sqlite3.connect('blacklist.db')
    c = conn.cursor()
    c.execute('SELECT * FROM scams WHERE url = ?', (url,))
    data = c.fetchone()
    conn.close()
    return data


# 2. AI LOGIC (Rate-Limit Protected & Context Aware)
# app.py (near the top)

# This tells Python to look into your secrets.toml file
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def get_ai_score(text):
    prompt = f"""
    Analyze this message for an Indian shopkeeper: '{text}'

    RULES:
    1. If the message is a FRIENDLY update (e.g. 'Order packed', 'Meeting at 4 PM') WITHOUT a suspicious link, return 0.0.
    2. If it is a standard OTP/Bank notification from a verified source, return 0.0.
    3. Return 1.0 ONLY if there is a 'Panic' threat (Electricity cut, Account blocked) or a suspicious phishing URL.

    Reply ONLY with a number between 0.0 and 1.0.
    """
    try:
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return float(response.text.strip())
    except errors.ClientError as e:
        if "429" in str(e):
            time.sleep(10)  # Cooling off
            try:
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                return float(response.text.strip())
            except:
                return 0.5
        return 0.5
    except:
        return 0.5


# 3. CONFIGURATION
WHITELIST = ["google.com", "amazon.in", "sbi.co.in", "gov.in", "paytm.com", "bescom.co.in"]
SAFE_KEYWORDS = ["packed", "shipped", "meeting", "greetings", "hello", "scheduled"]
init_db()

st.set_page_config(page_title="Bharat Phish-Guard", page_icon="🛡️", layout="centered")

# --- UI HEADER ---
st.title("🛡️ Bharat Phish-Guard")
st.markdown("### Digital Security for Indian Shopkeepers")
st.write("Ensuring your business stays safe from digital fraud.")

user_input = st.text_input("Paste Link or Message here:", placeholder="Paste suspicious text here...")

# --- MAIN SCAN BUTTON ---
if st.button("🔍 Run Full Security Scan", use_container_width=True):
    if user_input:
        # LAYER 1: WHITELIST & SAFE-WORD BYPASS
        is_safe_msg = any(word in user_input.lower() for word in SAFE_KEYWORDS)
        has_link = "http" in user_input.lower()

        # Check Whitelist
        if any(domain in user_input.lower() for domain in WHITELIST):
            st.balloons()  # 🎉 Celebration!
            st.success("✅ VERIFIED OFFICIAL: This is a trusted government or bank domain.")

        # Check Safe Business Context
        elif is_safe_msg and not has_link:
            st.balloons()  # 🎉 Celebration!
            st.success("✅ SAFE: This appears to be a normal business update.")
            st.info("Context: Order Update / Meeting Notification.")

        # LAYER 2: COMMUNITY BLACKLIST
        elif is_blacklisted(user_input):
            data = is_blacklisted(user_input)
            st.error(f"🚨 ALREADY REPORTED: This link is in our Community Blacklist!")
            st.metric("Known Risk", f"{data[1]}%")

        # LAYER 3: LIVE HYBRID ANALYSIS (ML + AI + TECH)
        else:
            with st.spinner("Analyzing Tech, AI & ML Layers..."):
                # Technical Check
                is_https = user_input.lower().startswith("https://")
                tech_risk = 0.0 if is_https else 0.8

                # AI Check
                ai_prob = get_ai_score(user_input)

                # ML Check
                ml_model = joblib.load('phish_model.pkl')
                ml_prob = ml_model.predict_proba([extract_features(user_input)])[0][1]

                # Final Logic Calculation
                final_risk = (ai_prob * 0.5) + (ml_prob * 0.3) + (tech_risk * 0.2)

                st.divider()

                if final_risk >= 0.60:
                    st.error("🛑 DO NOT CLICK / DO NOT PAY")
                    cols = st.columns(3)
                    cols[0].metric("Risk Level", "DANGER")
                    cols[1].metric("Technical", "INSECURE" if not is_https else "SECURE")
                    cols[2].metric("Context", "SUSPICIOUS")

                    if st.button("🚩 Add to Community Blacklist"):
                        add_to_blacklist(user_input, round(final_risk * 100, 2))
                        st.toast("Added to Blacklist!")
                else:
                    st.balloons()  # 🎉 Celebration for new safe links!
                    st.success(f"✅ PROCEED WITH CAUTION ({final_risk * 100:.1f}%)")
                    st.info("This link does not show typical scam patterns.")
    else:
        st.warning("Please enter something to scan.")

st.divider()
st.caption("Bharat Phish-Guard v1.3 | Powered by Gemini & Random Forest")