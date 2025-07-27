python
# ===============================
# 📦 LogiBot AI Copilot – Main App
# ===============================
# This is the main Streamlit application file for LogiBot, an AI Copilot
# designed to assist with logistics manifest analysis.

# --- Imports ---
import streamlit as st # Streamlit library for creating interactive web applications.
import pandas as pd # Pandas library for data manipulation and analysis, especially DataFrames.
from langchain.docstore.document import Document # Document class from LangChain, used to represent text content for LLM processing.

# --- Custom modules from your project ---
# These imports bring in functions and configurations from other Python files
# within the LogiBot project structure.
from config import OPENAI_API_KEY # Imports the OpenAI API key from a 'config.py' file for secure access.
from utils.llm_utils import summarize_manifest, answer_question # Imports LLM utility functions for summarization and Q&A.
from utils.carrier_utils import load_approved_carriers, save_approved_carriers # Imports utilities for managing a list of approved carriers.
from utils.pdf_utils import generate_pdf # Imports a utility to generate PDF reports (though not directly used in the main flow here).
from utils.email_utils import send_email_alert # Imports a utility to send email alerts.
from utils.excel_utils import export_manifest_to_excel # Imports a utility to export data to Excel.
from tabs.shipment_alert_tab import shipment_alert_tab  # ✅ NEW: Imports the function that defines the content and logic for the "Shipment Alerts" tab.

# --- Streamlit Page Configuration ---
# Sets global configurations for the Streamlit page.
st.set_page_config(page_title="LogiBot AI Copilot", layout="wide") # Sets the browser tab title and uses a wide layout for the app.
st.title("📦 LogiBot – AI Copilot for Logistics") # Displays the main title of the application on the page, with an emoji.

# --- Upload Section ---
# Allows users to upload a logistics manifest file.
uploaded_file = st.file_uploader(
    "Upload logistics manifest (CSV or Excel)", # Label for the file uploader widget.
    type=["csv", "xlsx"] # Specifies allowed file types (CSV and Excel).
)

# --- If a file is uploaded, process it ---
# This block of code executes only if a file has been successfully uploaded by the user.
if uploaded_file:
    try:
        # --- Load the file into a DataFrame ---
        # Reads the uploaded file into a pandas DataFrame based on its file extension.
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

        # --- Clean column names: lowercase, strip spaces ---
        # Standardizes column names by removing leading/trailing spaces, converting to lowercase,
        # and replacing spaces within names with an empty string. This helps with consistent data access.
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "")

        # --- Show success message and preview ---
        st.success("✅ Manifest loaded.") # Displays a success message with an emoji.
        st.dataframe(df.head()) # Shows the first few rows of the loaded DataFrame as a preview.

        # --- Prepare the text for summarisation & Q&A ---
        # Converts the DataFrame content into a CSV string, which is then wrapped in a LangChain Document object.
        # This format is suitable for input to Large Language Models (LLMs) for summarization and question answering.
        text_data = df.to_csv(index=False) # Converts DataFrame to CSV string without the pandas index.
        documents = [Document(page_content=text_data)] # Creates a list of LangChain Document objects from the text data.

        # --- Create 5 functional tabs for the app ---
        # Defines five tabs at the top of the application, each with a title and an emoji.
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Summary", # Tab for AI-powered manifest summary.
            "💬 Q&A", # Tab for asking questions about the manifest data.
            "⚙️ Settings", # Tab for managing application settings, like approved carriers.
            "📤 Export", # Tab for exporting data and reports.
            "🚨 Shipment Alerts"  # ✅ NEW Tab: Tab dedicated to handling shipment delay alerts.
        ])

        # ===============================
        # 📋 Tab 1: AI Summary
        # ===============================
        with tab1: # Content for the "Summary" tab.
            # Button to trigger manifest summarization.
            if st.button("Summarise Manifest"):
                # Calls a utility function to summarize the manifest using an LLM.
                summary = summarize_manifest(text_data, OPENAI_API_KEY)
                st.markdown("### 📋 AI Summary") # Displays a subheader for the summary.
                st.write(summary) # Writes the generated summary to the Streamlit app.

        # ===============================
        # 💬 Tab 2: Manifest Q&A
        # ===============================
        with tab2: # Content for the "Q&A" tab.
            # Text input field for the user to ask questions.
            user_question = st.text_input("Ask LogiBot a question:")
            # If a question is entered, trigger the Q&A process.
            if user_question:
                # Calls a utility function to answer the question using an LLM and the manifest documents.
                result = answer_question(documents, user_question, OPENAI_API_KEY)
                st.markdown("### 💬 Answer") # Displays a subheader for the answer.
                st.write(result) # Writes the LLM's answer to the Streamlit app.

        # ===============================
        # ⚙️ Tab 3: Carrier Settings
        # ===============================
        with tab3: # Content for the "Settings" tab.
            # --- View/Edit Approved Carriers ---
            st.markdown("### ⚙️ Manage Approved Carriers") # Subheader for carrier management.
            current = load_approved_carriers() # Loads the currently approved carriers from storage.
            # Text area to display and edit the list of approved carriers.
            edited = st.text_area("Approved carriers (comma-separated)", ", ".join(current))
            # Button to save changes to the carrier list.
            if st.button("Update Carrier List"):
                # Saves the updated list of carriers, cleaning and standardizing input.
                save_approved_carriers([x.strip().lower() for x in edited.split(",")])
                st.success("Carrier list updated.") # Confirmation message.

            # --- Send a test compliance email ---
            st.markdown("---") # Horizontal rule for visual separation.
            st.markdown("### 📧 Send Test Alert") # Subheader for sending test emails.
            recipient = st.text_input("Send alert to email:") # Input field for the recipient's email address.
            # Button to send a test email alert.
            if st.button("Send Test Email") and recipient:
                # Calls a utility function to send the email.
                sent = send_email_alert("LogiBot Alert", "Test compliance alert.", recipient)
                if sent:
                    st.success("Test email sent.") # Success message if email is sent.

        # ===============================
        # 📤 Tab 4: Export to Excel
        # ===============================
        with tab4: # Content for the "Export" tab.
            st.markdown("### 📤 Export Summary & Data") # Subheader for export options.

            # Generate summary & dummy compliance notes
            # Re-summarizes the manifest for inclusion in the export.
            summary = summarize_manifest(text_data, OPENAI_API_KEY)
            # 🔧 Placeholder: Defines dummy compliance notes for demonstration purposes.
            # compliance_notes = ["SHP003 missing tracking ID", "Carrier XYZ not approved"]
            compliance_notes = []
            if "carrier" in df.columns:
                approved_carriers = load_approved_carriers()
                for i, row in df.iterrows():
                    carrier = str(row["carrier"]).strip().lower()
                    if carrier not in approved_carriers:
                        compliance_notes.append(f"{row.get('shipmentid', f'Row {i+2}')} uses unapproved carrier: {carrier}")

            if "trackingid" in df.columns:
                for i, row in df.iterrows():
                    if pd.isna(row["trackingid"]) or str(row["trackingid"]).strip() == "":
                        compliance_notes.append(f"{row.get('shipmentid', f'Row {i+2}')} missing tracking ID")

            # Export to Excel
            # Calls a utility function to export the DataFrame, summary, and compliance notes to an Excel file.
            excel_path = export_manifest_to_excel(df, summary, compliance_notes)

            # Download button
            # Provides a button for the user to download the generated Excel report.
            with open(excel_path, "rb") as f: # Opens the generated Excel file in binary read mode.
                st.download_button(
                    "📥 Download Excel Report", # Label for the download button.
                    data=f, # The file data to be downloaded.
                    file_name=excel_path.split("/")[-1], # Sets the downloaded file name to just the file name from the path.
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" # Specifies the MIME type for Excel files.
                )

        # ===============================
        # 🚨 Tab 5: Shipment Delay Alert (LangChain + Email)
        # ===============================
        with tab5: # Content for the "Shipment Alerts" tab.
            # ✅ Executes the function imported from 'shipment_alert_tab.py'.
            # This function likely contains the logic for detecting delayed shipments
            # using LangChain and offering options to send email alerts.
            shipment_alert_tab()

    # --- Error Handling for File Upload ---
    # Catches any exceptions that occur during file loading or initial processing.
    except Exception as e:
        st.error(f"❌ Error loading file: {e}") # Displays an error message to the user.

# --- UI when no file is uploaded ---
# This block is displayed when no file has been uploaded yet.
else:
    st.info("📂 Please upload a manifest file to get started.") # Informational message prompting file upload.