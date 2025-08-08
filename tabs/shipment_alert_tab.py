# ======================================================
# tabs/shipment_alert_tab.py
# This module contains the function to display the
# shipment alert dashboard tab.
# Updated to use ColumnMapper for robust column handling
# ======================================================

import streamlit as st
import pandas as pd
from jinja2 import Template
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
from utils.email_utils import send_email_alert
from utils.column_utils import ColumnMapper  # Add this import

# Updated template to use display names
multi_prompt_template = """
🤖 **LogiBot's Answer**

{{ delay_count }} shipment{{ 's' if delay_count > 1 else '' }} currently delayed:

{% for s in shipments %}
- **{{ shipment_id_display }}:** {{ s.shipmentid }}
  • **{{ status_display }}:** {{ s.status }}
  • **{{ eta_display }}:** {{ s.expectedarrival }}
  • **Action:** {{ s.action }}
{% endfor %}
"""

def format_multi_shipment_alert(shipments: list, display_names: dict = None) -> str:
    """
    Renders a delay summary using the Jinja2 template and provided shipment data.
    Now supports custom display names for column headers.
    """
    tm = Template(multi_prompt_template)
    delay_count = len(shipments)
    
    # Set default display names or use provided ones
    if not display_names:
        display_names = {
            'shipmentid': 'Shipment ID',
            'status': 'Status', 
            'expectedarrival': 'ETA'
        }
    
    return tm.render(
        shipments=shipments, 
        delay_count=delay_count,
        shipment_id_display=display_names.get('shipmentid', 'Shipment ID'),
        status_display=display_names.get('status', 'Status'),
        eta_display=display_names.get('expectedarrival', 'ETA')
    )

def rewrite_tone(message: str, tone: str) -> str:
    """
    Rewrites a message in a specified tone using an LLM.
    """
    # Keep your existing simplified mock response approach
    if tone == "urgent":
        return f"🚨 URGENT: There are {message.count('Shipment ID:')} delayed shipments. Please review the details immediately: {message}"
    elif tone == "formal":
        return f"Please be advised that the following shipments are currently delayed: {message}"
    else:
        return message


def find_column_case_insensitive(df: pd.DataFrame, target_patterns: list) -> str:
    """
    Find a column that matches any of the target patterns (case-insensitive).
    
    Args:
        df (pd.DataFrame): DataFrame to search
        target_patterns (list): List of possible column name patterns to match
    
    Returns:
        str or None: Actual column name if found, None otherwise
    """
    df_columns_lower = [col.lower() for col in df.columns]
    
    for pattern in target_patterns:
        pattern_lower = pattern.lower()
        if pattern_lower in df_columns_lower:
            # Return the actual column name (with original case)
            idx = df_columns_lower.index(pattern_lower)
            return df.columns[idx]
    
    return None


def shipment_alert_tab(df: pd.DataFrame):
    """
    The Streamlit tab that allows users to:
    - View delayed shipments
    - Rephrase the alert message  
    - Send it to their email
    Now uses case-insensitive column detection.

    Args:
        df (pd.DataFrame): The normalized manifest data from the uploaded file.
    """
    st.header("🚨 Shipment Alerts")
    st.write("Track delayed and upcoming shipments to stay on top of your logistics.")

    if df is None or df.empty:
        st.info("Please upload a manifest file to check for delayed shipments.")
        return

    # --- Updated Case-Insensitive Column Detection ---
    # Define possible column name patterns for each field
    shipment_id_patterns = [
        'shipment_id', 'shipmentid', 'shipment id', 'id', 'tracking_number', 
        'tracking number', 'tracking_ref', 'tracking ref', 'reference'
    ]
    
    status_patterns = [
        'status', 'shipment_status', 'shipment status', 'delivery_status', 'delivery status'
    ]
    
    expected_arrival_patterns = [
        'expected_arrival', 'expectedarrival', 'expected arrival', 'eta', 
        'delivery_date', 'delivery date', 'expected_delivery', 'expected delivery'
    ]
    
    carrier_patterns = [
        'carrier', 'carrier_name', 'carrier name', 'shipping_company', 'shipping company'
    ]

    # Find actual columns using case-insensitive search
    shipment_id_col = find_column_case_insensitive(df, shipment_id_patterns)
    status_col = find_column_case_insensitive(df, status_patterns)
    expected_arrival_col = find_column_case_insensitive(df, expected_arrival_patterns)
    carrier_col = find_column_case_insensitive(df, carrier_patterns)
    
    # Check if we have the minimum required columns
    if not status_col:
        st.warning(
            "Analysis not applicable for this document type. "
            "Select a manifest file with a Status column."
        )
        return
    
    if not shipment_id_col:
        st.warning(
            "No Shipment ID column found. "
            "Shipment identification may be limited."
        )
    
    # --- Delayed Shipments ---
    st.subheader("Delayed Shipments")
    
    # Filter delayed shipments using the found column (case-insensitive)
    delayed_shipments = df[df[status_col].str.lower().str.contains('delay', na=False)]
    
    if delayed_shipments.empty:
        st.success("✅ All shipments are currently on time.")
        return

    # Show delayed shipments with proper display names
    st.info(f"⚠️ Found {len(delayed_shipments)} delayed shipment(s)")
    
    # Create display version for showing to user with proper column names
    display_delayed = delayed_shipments.copy()
    
    # Rename columns to proper display names
    column_rename_map = {}
    if shipment_id_col:
        column_rename_map[shipment_id_col] = 'Shipment ID'
    if status_col:
        column_rename_map[status_col] = 'Status'
    if expected_arrival_col:
        column_rename_map[expected_arrival_col] = 'Expected Arrival'
    if carrier_col:
        column_rename_map[carrier_col] = 'Carrier'
    
    # Apply ColumnMapper display formatting to other columns
    for col in display_delayed.columns:
        if col not in column_rename_map:
            column_rename_map[col] = ColumnMapper.get_display_name(col)
    
    display_delayed = display_delayed.rename(columns=column_rename_map)
    st.dataframe(display_delayed, use_container_width=True)

    # Convert filtered DataFrame to a list of dictionaries for templating
    delayed_list = []
    for _, row in delayed_shipments.iterrows():
        shipment_data = {
            'shipmentid': row[shipment_id_col] if shipment_id_col else 'N/A',
            'status': row[status_col],
            'expectedarrival': row[expected_arrival_col] if expected_arrival_col else 'N/A',
            'action': "Contact the carrier for an updated ETA."
        }
        delayed_list.append(shipment_data)

    # Choose tone
    tone = st.selectbox("Choose tone for the alert message:", ["friendly", "urgent", "formal"])

    # Generate message using proper display names
    display_names = {
        'shipmentid': 'Shipment ID',
        'status': 'Status',
        'expectedarrival': 'Expected Arrival'
    }
    
    base_msg = format_multi_shipment_alert(delayed_list, display_names)
    rewritten_msg = rewrite_tone(base_msg, tone)

    # Show final message
    st.markdown("### ✉️ LogiBot's Generated Alert:")
    st.markdown(rewritten_msg)

    # Email input and send - Updated to match your email function signature
    recipient = st.text_input("Enter recipient email:")
    if st.button("Send Alert Email"):
        if recipient:
            success = send_email_alert(
                subject=f"LogiBot Alert: {len(delayed_list)} Shipments Delayed",
                body=rewritten_msg,
                to_email=recipient  # Your function uses 'to_email' parameter
            )
            if success:
                st.success(f"Alert email sent to {recipient}!")
            else:
                st.error("Failed to send email. Please check your email configuration.")
        else:
            st.warning("Please enter a valid recipient email address.")
            
    # Additional features
    st.subheader("📊 Additional Options")
    
    # Export delayed shipments
    if st.button("📄 Export Delayed Shipments"):
        csv_data = display_delayed.to_csv(index=False)
        st.download_button(
            label="💾 Download CSV",
            data=csv_data,
            file_name=f"delayed_shipments_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Show summary statistics with display names
    with st.expander("📊 Delay Statistics"):
        st.write(f"**Total delayed shipments:** {len(delayed_shipments)}")
        st.write(f"**Percentage of total:** {(len(delayed_shipments) / len(df) * 100):.1f}%")
        
        # Breakdown by carrier if available
        if carrier_col:
            delayed_by_carrier = delayed_shipments[carrier_col].value_counts()
            st.write("**Delays by Carrier:**")
            for carrier, count in delayed_by_carrier.items():
                st.write(f"• {carrier}: {count} shipment{'s' if count > 1 else ''}")