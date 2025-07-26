import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_FROM

def send_email_alert(subject, body, to_email):
    """
    Sends an email using SSL (required for Zoho SMTP on port 465).
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = to_email

    try:
        # ✅ Zoho requires SSL (not starttls) on port 465
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, to_email, msg.as_string())

        return True
    except Exception as e:
        print(f"[Email Error] {e}")
        return False
