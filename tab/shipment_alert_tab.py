import streamlit as st
import csv
from jinja2 import Template
from app.utils.email_sender import send_email
from langchain.prompts import PromptTemplate
from langchain_community.llms import OpenAI  # Replace or mock if not using OpenAI

# Load and filter delayed shipments from CSV
def load_delayed_shipments_from_csv(path="data/shipments.csv"):
    """
    Loads shipment data and returns only those marked as delayed.
    """
    delayed = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'].lower().startswith('delayed'):
                delayed.append({
                    "shipment_id": row["shipment_id"],
                    "status": row["status"],
                    "eta": row["eta"],
                    "action": row["action"]
                })
    return delayed

# Format the LangChain delay summary using Jinja2-style templating
def format_multi_shipment_alert(shipments: list) -> str:
    """
    Renders a summary of delayed shipments as a human-readable message.
    """
    multi_prompt_template = """
    🤖 **LogiBot's Answer**

    {{ delay_count }} shipment{{ 's' if delay_count > 1 else '' }} currently delayed:

    {% for s in shipments %}
    - **Shipment ID:** {{ s.shipment_id }}
      • **Status:** {{ s.status }}
      • **ETA:** {{ s.eta }}
      • **Action:** {{ s.action }}
    {% endfor %}
    """
    tmpl = Template(multi_prompt_template)
    return tmpl.render(shipments=shipments, delay_count=len(shipments))

# Rewrites the summary using an LLM for tone adjustment
def rewrite_tone(message: str, tone: str = "friendly") -> str:
    """
    Uses LangChain + OpenAI to rephrase the alert message in a specific tone.
    """
    prompt_template = PromptTemplate.from_template("""
    Rewrite the following message in a {tone} tone:

    "{message}"
    """)
    final_prompt = prompt_template.format(tone=tone, message=message)

    # Replace with mock logic if no API access
    llm = OpenAI(temperature=0.7)
    return llm.invoke(final_prompt)

# Render the entire Streamlit tab
def shipment_alert_tab():
    """
    The Streamlit tab that allows users to:
    - View delayed shipments
    - Rephrase the alert message
    - Send it to their email
    """
    st.markdown("## 📦 Shipment Delay Alert")

    # Load delay data
    delayed_shipments = load_delayed_shipments_from_csv()

    if not delayed_shipments:
        st.success("✅ All shipments are currently on time.")
        return

    # Choose tone
    tone = st.selectbox("Choose tone for the alert message:", ["friendly", "urgent", "formal"])

    # Generate message
    base_msg = format_multi_shipment_alert(delayed_shipments)
    rewritten_msg = rewrite_tone(base_msg, tone)

    # Show final message
    st.markdown("### ✉️ LogiBot's Generated Alert:")
    st.markdown(rewritten_msg)

    # Email input and send
    recipient = st.text_input("Enter recipient email:")
    if st.button("Send Alert Email"):
        if recipient:
            send_email(
                subject="🚨 Shipment Delay Alert",
                body=rewritten_msg,
                to_email=recipient
            )
            st.success(f"Email sent to {recipient}")
        else:
            st.error("Please enter a valid email address.")
