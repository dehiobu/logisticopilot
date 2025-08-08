
from utils.email_utils import send_email_alert

# Test parameters (update these if needed)
subject = "Test: LogiBot Email Integration"
body = "This is a test email sent via Zoho SMTP using SSL."
recipient = "your_email@example.com"  # ✅ Replace with your actual test email

# Attempt to send the email
success = send_email_alert(subject, body, recipient)

if success:
    print("✅ Email sent successfully.")
else:
    print("❌ Email failed to send. Check SMTP settings or credentials.")
