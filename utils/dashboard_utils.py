import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional

# --- Helper function for case-insensitive column finding ---
def find_column(df: pd.DataFrame, target_name: str) -> Optional[str]:
    """
    Finds a column in a DataFrame by a case-insensitive name.
    Returns the actual column name or None if not found.
    """
    for col in df.columns:
        if col.lower() == target_name.lower():
            return col
    return None

def display_key_metrics(df: pd.DataFrame):
    """
    Display high-level shipment KPIs across the manifest.
    Handles cases where expected columns are missing or have inconsistent casing.
    """
    status_col = find_column(df, "status")
    if not status_col:
        st.warning("The uploaded manifest does not contain a 'status' column. Key metrics cannot be displayed.")
        return

    total = len(df)
    delayed = df[status_col].str.lower().str.contains("delay", na=False).sum()
    transit = df[status_col].str.lower().str.contains("in transit", na=False).sum()
    complete = df[status_col].str.lower().str.contains("delivered|completed", na=False).sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Shipments", total)
    col2.metric("🔴 Delayed", delayed)
    col3.metric("🟡 In Transit", transit)
    col4.metric("✅ Completed", complete)


def plot_status_chart(df: pd.DataFrame):
    """
    Show a bar chart of shipment status counts.
    Handles cases where the 'status' column is missing or has inconsistent casing.
    """
    status_col = find_column(df, "status")
    if not status_col:
        st.warning("Cannot plot status chart: 'status' column not found in manifest.")
        return

    status_counts = df[status_col].str.title().value_counts()
    fig, ax = plt.subplots()
    status_counts.plot(kind="bar", ax=ax, color="skyblue")
    ax.set_title("Shipment Status Overview")
    ax.set_ylabel("Count")
    ax.set_xlabel("Status")
    st.pyplot(fig)


def plot_carrier_pie(df: pd.DataFrame):
    """
    Show pie chart of top carriers in the manifest.
    Handles cases where the 'carrier' column is missing or has inconsistent casing.
    """
    carrier_col = find_column(df, "carrier")
    if not carrier_col:
        st.warning("Cannot plot carrier pie chart: 'carrier' column not found in manifest.")
        return

    carrier_counts = df[carrier_col].value_counts()
    # Plot only the top 5 carriers, grouping the rest into 'Other'
    top_carriers = carrier_counts.nlargest(5)
    other_count = carrier_counts.iloc[5:].sum()

    if other_count > 0:
        top_carriers["Other"] = other_count
    
    fig, ax = plt.subplots()
    ax.pie(top_carriers, labels=top_carriers.index, autopct="%1.1f%%", startangle=90, colors=plt.cm.Paired.colors)
    ax.axis("equal") # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title("Top Carriers Distribution")
    st.pyplot(fig)
