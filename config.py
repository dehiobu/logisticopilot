# config.py
import streamlit as st

# Load API Keys and SMTP config from Streamlit Secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ALERT_EMAIL_FROM = st.secrets["ALERT_EMAIL_FROM"]
SMTP_SERVER = st.secrets["SMTP_SERVER"]
SMTP_PORT = int(st.secrets.get("SMTP_PORT", 587))  # Default to 587 if not set
SMTP_USER = st.secrets["SMTP_USER"]
SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]

# Optional: Debug visibility
print(f"DEBUG_SECRET_CHECK: OPENAI_API_KEY: '{OPENAI_API_KEY}'")