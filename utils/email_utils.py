import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_FROM

def send_email_alert(subject, body, to_email):
    """
    Sends an email using SSL (Zoho compatible), with explicit connect() call.
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = to_email

    try:
        # 🔧 Create SMTP_SSL object and explicitly connect
        server = smtplib.SMTP_SSL()
        server.connect(SMTP_SERVER, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(ALERT_EMAIL_FROM, to_email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print(f"[Email Error] {e}")
        return False
