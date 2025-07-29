# config.py
import streamlit as st
import os

def get_secret(key: str, fallback: str = None):
    """Retrieve value from Streamlit secrets or fall back to environment variable."""
    return st.secrets.get(key) or os.getenv(key) or fallback

# Load values from secrets or env vars
OPENAI_API_KEY     = get_secret("OPENAI_API_KEY")
ALERT_EMAIL_FROM   = get_secret("ALERT_EMAIL_FROM")
SMTP_SERVER        = get_secret("SMTP_SERVER")
SMTP_PORT          = int(get_secret("SMTP_PORT", "587"))  # Default to 587
SMTP_USER          = get_secret("SMTP_USER")
SMTP_PASSWORD      = get_secret("SMTP_PASSWORD")

# Optional debug
print(f"DEBUG_SECRET_CHECK: OPENAI_API_KEY: '{OPENAI_API_KEY}'")