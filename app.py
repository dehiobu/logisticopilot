import streamlit as st
import pandas as pd
from langchain.docstore.document import Document

from config import OPENAI_API_KEY
from utils.llm_utils import summarize_manifest, answer_question
from utils.carrier_utils import load_approved_carriers, save_approved_carriers
from utils.pdf_utils import generate_pdf
from utils.email_utils import send_email_alert
from utils.excel_utils import export_manifest_to_excel

st.set_page_config(page_title="LogiBot AI Copilot", layout="wide")
st.title("📦 LogiBot – AI Copilot for Logistics")

uploaded_file = st.file_uploader("Upload logistics manifest (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "")

        st.success("✅ Manifest loaded.")
        st.dataframe(df.head())

        text_data = df.to_csv(index=False)
        documents = [Document(page_content=text_data)]

        tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "💬 Q&A", "⚙️ Settings", "📤 Export"])

        # --- Summary Tab ---
        with tab1:
            if st.button("Summarise Manifest"):
                summary = summarize_manifest(text_data, OPENAI_API_KEY)
                st.markdown("### 📋 AI Summary")
                st.write(summary)

        # --- Q&A Tab ---
        with tab2:
            user_question = st.text_input("Ask LogiBot a question:")
            if user_question:
                result = answer_question(documents, user_question, OPENAI_API_KEY)
                st.markdown("### 💬 Answer")
                st.write(result)

        # --- Settings Tab ---
        with tab3:
            st.markdown("### ⚙️ Manage Approved Carriers")
            current = load_approved_carriers()
            edited = st.text_area("Approved carriers (comma-separated)", ", ".join(current))
            if st.button("Update Carrier List"):
                save_approved_carriers([x.strip().lower() for x in edited.split(",")])
                st.success("Carrier list updated.")

            st.markdown("---")
            st.markdown("### 📧 Send Test Alert")
            recipient = st.text_input("Send alert to email:")
            if st.button("Send Test Email") and recipient:
                sent = send_email_alert("LogiBot Alert", "Test compliance alert.", recipient)
                if sent:
                    st.success("Test email sent.")

        # --- Export Tab ---
        with tab4:
            st.markdown("### 📤 Export Summary & Data")
            summary = summarize_manifest(text_data, OPENAI_API_KEY)
            compliance_notes = ["SHP003 missing tracking ID", "Carrier XYZ not approved"]  # Placeholder
            excel_path = export_manifest_to_excel(df, summary, compliance_notes)

            with open(excel_path, "rb") as f:
                st.download_button("📥 Download Excel Report", data=f, file_name=excel_path.split("/")[-1], mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
else:
    st.info("📂 Please upload a manifest file to get started.")