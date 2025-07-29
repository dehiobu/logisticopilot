    # config.py
    import os

    # Load API Keys and other secure configs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # --- TEMPORARY DEBUG LINE ---
    print(f"DEBUG_SECRET_CHECK: OPENAI_API_KEY raw value: '{OPENAI_API_KEY}' (Type: {type(OPENAI_API_KEY)})")
    # --- END TEMPORARY DEBUG LINE ---

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set. Please set it securely.")

    ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
    if not ALERT_EMAIL_FROM:
        raise ValueError("ALERT_EMAIL_FROM environment variable not set.")

    SMTP_SERVER = os.getenv("SMTP_SERVER")
    if not SMTP_SERVER:
        raise ValueError("SMTP_SERVER environment variable not set.")

    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    if not SMTP_PORT:
        raise ValueError("SMTP_PORT environment variable not set or invalid.")

    SMTP_USER = os.getenv("SMTP_USER")
    if not SMTP_USER:
        raise ValueError("SMTP_USER environment variable not set.")

    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    if not SMTP_PASSWORD:
        raise ValueError("SMTP_PASSWORD environment variable not set.")
    