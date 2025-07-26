import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def display_key_metrics(df):
    """
    Display high-level shipment KPIs across the manifest.
    """
    total = len(df)
    delayed = df["status"].str.lower().str.contains("delay").sum()
    transit = df["status"].str.lower().str.contains("in transit").sum()
    complete = df["status"].str.lower().str.contains("delivered|completed").sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Shipments", total)
    col2.metric("🔴 Delayed", delayed)
    col3.metric("🟡 In Transit", transit)
    col4.metric("✅ Completed", complete)


def plot_status_chart(df):
    """
    Show a bar chart of shipment status counts.
    """
    if "status" not in df.columns:
        st.warning("No 'status' column found.")
        return

    status_counts = df["status"].str.title().value_counts()
    fig, ax = plt.subplots()
    status_counts.plot(kind="bar", ax=ax, color="skyblue")
    ax.set_title("Shipment Status Overview")
    ax.set_ylabel("Count")
    ax.set_xlabel("Status")
    st.pyplot(fig)


def plot_carrier_pie(df):
    """
    Show pie chart of top carriers in the manifest.
    """
    if "carrier" not in df.columns:
        st.warning("No 'carrier' column found.")
        return

    carrier_counts = df["carrier"].str.title().value_counts().head(5)
    fig, ax = plt.subplots()
    carrier_counts.plot(kind="pie", ax=ax, autopct='%1.1f%%', startangle=90)
    ax.set_ylabel("")
    ax.set_title("Top 5 Carriers")
    st.pyplot(fig)
