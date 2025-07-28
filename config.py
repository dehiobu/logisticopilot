# config.py
import os
# If running locally and using a .env file, you'd also need:
# from dotenv import load_dotenv
# load_dotenv() # This loads variables from .env into os.environ

# Load API Keys and other secure configs from environment variables
# The string inside os.getenv() should be the NAME of the environment variable.

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Reads the value of the environment variable named "OPENAI_API_KEY"
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set. Please set it securely.")

ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
if not ALERT_EMAIL_FROM:
    raise ValueError("ALERT_EMAIL_FROM environment variable not set.")

SMTP_SERVER = os.getenv("SMTP_SERVER")
if not SMTP_SERVER:
    raise ValueError("SMTP_SERVER environment variable not set.")

SMTP_PORT = int(os.getenv("SMTP_PORT", 587)) # Reads "SMTP_PORT", defaults to 587 if not set
if not SMTP_PORT: # Check if it's still not set (e.g., if default was 0 or invalid)
    raise ValueError("SMTP_PORT environment variable not set or invalid.")

SMTP_USER = os.getenv("SMTP_USER")
if not SMTP_USER:
    raise ValueError("SMTP_USER environment variable not set.")

SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    raise ValueError("SMTP_PASSWORD environment variable not set.")