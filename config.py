# ==============================================================================
# ⚙️ Configuration Management - Enhanced Version
# ==============================================================================
import streamlit as st
import os
import warnings
from typing import Optional, Union


def get_secret(key: str, fallback: str = None) -> Optional[str]:
    """
    Retrieve value from Streamlit secrets, environment variables, or fallback.
    
    Args:
        key (str): The key to look for
        fallback (str, optional): Fallback value if key is not found
        
    Returns:
        Optional[str]: The found value or None
    """
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and key in st.secrets:
            value = st.secrets[key]
            if value and str(value).strip():
                return str(value).strip()
    except Exception:
        pass
    
    # Try environment variables
    env_value = os.getenv(key)
    if env_value and env_value.strip():
        return env_value.strip()
    
    # Return fallback
    return fallback


def validate_config() -> dict:
    """
    Validate configuration and return status information.
    
    Returns:
        dict: Configuration validation status
    """
    validation_results = {
        'openai_api_key': bool(OPENAI_API_KEY and len(OPENAI_API_KEY) > 10),
        'email_config': bool(ALERT_EMAIL_FROM and SMTP_SERVER and SMTP_USER and SMTP_PASSWORD),
        'smtp_config': bool(SMTP_SERVER and SMTP_PORT),
        'warnings': [],
        'errors': []
    }
    
    # Check OpenAI API Key
    if not validation_results['openai_api_key']:
        validation_results['errors'].append("OpenAI API key is missing or invalid")
    
    # Check email configuration
    if not validation_results['email_config']:
        missing_email_fields = []
        if not ALERT_EMAIL_FROM:
            missing_email_fields.append("ALERT_EMAIL_FROM")
        if not SMTP_SERVER:
            missing_email_fields.append("SMTP_SERVER")
        if not SMTP_USER:
            missing_email_fields.append("SMTP_USER")
        if not SMTP_PASSWORD:
            missing_email_fields.append("SMTP_PASSWORD")
        
        if missing_email_fields:
            validation_results['warnings'].append(
                f"Email alert functionality disabled. Missing: {', '.join(missing_email_fields)}"
            )
    
    # Check SMTP configuration
    if SMTP_PORT <= 0 or SMTP_PORT > 65535:
        validation_results['warnings'].append(f"Invalid SMTP port: {SMTP_PORT}. Using default 587.")
    
    return validation_results


# ------------------------------------------------------------------------------
# Configuration Values
# ------------------------------------------------------------------------------

# Load values from secrets or env vars
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
ALERT_EMAIL_FROM = get_secret("ALERT_EMAIL_FROM")
SMTP_SERVER = get_secret("SMTP_SERVER")
SMTP_PORT = int(get_secret("SMTP_PORT", "587"))  # Default to 587
SMTP_USER = get_secret("SMTP_USER")
SMTP_PASSWORD = get_secret("SMTP_PASSWORD")

# Additional configuration options
DEBUG_MODE = get_secret("DEBUG_MODE", "false").lower() == "true"
LOG_LEVEL = get_secret("LOG_LEVEL", "INFO").upper()
MAX_FILE_SIZE_MB = int(get_secret("MAX_FILE_SIZE_MB", "10"))
CACHE_TTL_MINUTES = int(get_secret("CACHE_TTL_MINUTES", "60"))

# App-specific settings
DEFAULT_CARRIERS = [
    "FedEx", "UPS", "DHL", "USPS", "Amazon Logistics",
    "OnTrac", "LaserShip", "GSO", "Purolator"
]

# LLM Configuration
LLM_MODEL = get_secret("LLM_MODEL", "gpt-3.5-turbo")
LLM_TEMPERATURE = float(get_secret("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(get_secret("LLM_MAX_TOKENS", "1000"))

# Retrieval Configuration
CHUNK_SIZE = int(get_secret("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(get_secret("CHUNK_OVERLAP", "200"))
RETRIEVAL_K = int(get_secret("RETRIEVAL_K", "5"))


# ------------------------------------------------------------------------------
# Validation and Debug Output
# ------------------------------------------------------------------------------

# Validate configuration
CONFIG_STATUS = validate_config()

# Debug output (only if DEBUG_MODE is enabled)
if DEBUG_MODE:
    print("=" * 50)
    print("🔧 LOGIBOT CONFIGURATION DEBUG")
    print("=" * 50)
    print(f"OPENAI_API_KEY: {'✅ Set' if OPENAI_API_KEY else '❌ Missing'}")
    print(f"SMTP_SERVER: '{SMTP_SERVER}'")
    print(f"SMTP_PORT: {SMTP_PORT}")
    print(f"SMTP_USER: {'✅ Set' if SMTP_USER else '❌ Missing'}")
    print(f"ALERT_EMAIL_FROM: {'✅ Set' if ALERT_EMAIL_FROM else '❌ Missing'}")
    print(f"LLM_MODEL: {LLM_MODEL}")
    print(f"LLM_TEMPERATURE: {LLM_TEMPERATURE}")
    print(f"MAX_FILE_SIZE_MB: {MAX_FILE_SIZE_MB}")
    print("=" * 50)

# Display warnings if any
if CONFIG_STATUS['warnings']:
    for warning in CONFIG_STATUS['warnings']:
        warnings.warn(f"LogiBot Config Warning: {warning}")

# Critical errors
if CONFIG_STATUS['errors']:
    for error in CONFIG_STATUS['errors']:
        print(f"❌ LogiBot Config Error: {error}")


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def is_api_key_valid() -> bool:
    """Check if OpenAI API key is properly configured."""
    return CONFIG_STATUS['openai_api_key']


def is_email_configured() -> bool:
    """Check if email alerts are properly configured."""
    return CONFIG_STATUS['email_config']


def get_config_summary() -> dict:
    """Get a summary of current configuration."""
    return {
        'openai_configured': is_api_key_valid(),
        'email_configured': is_email_configured(),
        'debug_mode': DEBUG_MODE,
        'model': LLM_MODEL,
        'max_file_size_mb': MAX_FILE_SIZE_MB,
        'smtp_server': SMTP_SERVER if SMTP_SERVER else 'Not configured',
        'smtp_port': SMTP_PORT
    }


def display_config_status():
    """Display configuration status in Streamlit (for admin/debug purposes)."""
    if not DEBUG_MODE:
        return
    
    config_summary = get_config_summary()
    
    st.subheader("🔧 Configuration Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**API Configuration:**")
        st.write(f"OpenAI API: {'✅' if config_summary['openai_configured'] else '❌'}")
        st.write(f"Model: {config_summary['model']}")
        
    with col2:
        st.write("**Email Configuration:**")
        st.write(f"Email Alerts: {'✅' if config_summary['email_configured'] else '❌'}")
        st.write(f"SMTP Server: {config_summary['smtp_server']}")
    
    if CONFIG_STATUS['warnings']:
        st.warning("Warnings: " + "; ".join(CONFIG_STATUS['warnings']))
    
    if CONFIG_STATUS['errors']:
        st.error("Errors: " + "; ".join(CONFIG_STATUS['errors']))


# Export commonly used configurations
__all__ = [
    'OPENAI_API_KEY',
    'ALERT_EMAIL_FROM', 
    'SMTP_SERVER',
    'SMTP_PORT',
    'SMTP_USER',
    'SMTP_PASSWORD',
    'DEFAULT_CARRIERS',
    'LLM_MODEL',
    'LLM_TEMPERATURE',
    'LLM_MAX_TOKENS',
    'is_api_key_valid',
    'is_email_configured',
    'get_config_summary',
    'display_config_status'
]