import smtplib
from email.mime.text import MIMEText
import ssl
import streamlit as st
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_FROM

def send_email_alert(subject, body, to_email):
    """
    Sends an email using SSL (Zoho compatible), with explicit connect() call.
    This version passes the hostname to the SMTP_SSL constructor for more reliable
    connection handling and avoids the 'server_hostname cannot be empty' error.
    
    Updated with better error handling and Streamlit integration.
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = to_email

    try:
        # Check if all required config variables are available
        missing_config = []
        if not SMTP_SERVER:
            missing_config.append("SMTP_SERVER")
        if not SMTP_PORT:
            missing_config.append("SMTP_PORT")
        if not SMTP_USER:
            missing_config.append("SMTP_USER")
        if not SMTP_PASSWORD:
            missing_config.append("SMTP_PASSWORD")
        if not ALERT_EMAIL_FROM:
            missing_config.append("ALERT_EMAIL_FROM")
            
        if missing_config:
            st.error(f"❌ Missing email configuration: {', '.join(missing_config)}")
            st.info("💡 Please configure your email settings in config.py")
            return False

        # Create a default SSL context for a more secure connection.
        context = ssl.create_default_context()
        
        # 🔧 Create SMTP_SSL object and explicitly connect.
        # Pass the server hostname to the constructor to ensure a proper
        # SSL handshake, resolving the reported error.
        with st.spinner("📧 Sending email..."):
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, to_email, msg.as_string())
            server.quit()

        st.success("✅ Email sent successfully!")
        return True
        
    except smtplib.SMTPAuthenticationError:
        st.error("❌ Email authentication failed. Please check your username and password.")
        return False
    except smtplib.SMTPRecipientsRefused:
        st.error("❌ Recipient email address was refused by the server.")
        return False
    except smtplib.SMTPServerDisconnected:
        st.error("❌ SMTP server connection was unexpectedly closed.")
        return False
    except Exception as e:
        st.error(f"❌ Email sending failed: {str(e)}")
        print(f"[Email Error] {e}")  # Keep your original logging
        return False

def test_email_configuration():
    """
    Test the email configuration without sending an actual email.
    Useful for debugging email setup issues.
    """
    st.subheader("📧 Test Email Configuration")
    
    if st.button("🔍 Test Email Settings"):
        try:
            # Test connection without sending
            context = ssl.create_default_context()
            with st.spinner("Testing connection..."):
                server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.quit()
            
            st.success("✅ Email configuration is working!")
            
        except Exception as e:
            st.error(f"❌ Email configuration test failed: {str(e)}")
            
            # Provide helpful debugging information
            st.info("**Debugging checklist:**")
            st.write("- Check SMTP server address and port")
            st.write("- Verify username and password") 
            st.write("- Ensure 'Less secure app access' is enabled (if using Gmail)")
            st.write("- Check if two-factor authentication requires an app password")

def configure_email_settings():
    """
    Streamlit UI for configuring email settings.
    This would typically be in a settings page or configuration tab.
    """
    st.subheader("📧 Email Configuration")
    st.info("Configure your SMTP settings to enable email alerts.")
    
    with st.form("email_config"):
        st.write("**Current Settings:**")
        st.code(f"""
SMTP_SERVER = "{SMTP_SERVER}"
SMTP_PORT = {SMTP_PORT}
SMTP_USER = "{SMTP_USER}"
ALERT_EMAIL_FROM = "{ALERT_EMAIL_FROM}"
SMTP_PASSWORD = "{'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'Not Set'}"
        """)
        
        st.write("**Common SMTP Settings:**")
        st.write("- **Gmail:** smtp.gmail.com, Port 587")
        st.write("- **Outlook:** smtp.live.com, Port 587") 
        st.write("- **Zoho:** smtp.zoho.com, Port 587")
        
        submitted = st.form_submit_button("ℹ️ Configuration Help")
        
        if submitted:
            st.info("""
            **To configure email settings:**
            1. Edit your `config.py` file
            2. Set the SMTP_* variables for your email provider
            3. Restart the application
            4. Use the 'Test Email Settings' button to verify
            """)