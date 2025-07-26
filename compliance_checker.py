"""
compliance_checker.py
----------------------

What this file does:
This Streamlit application allows users to upload customs documents (PDF or text format)
and uses a LangChain-powered AI agent (ComplianceBot) to detect missing or incorrect fields.
It simulates a compliance audit for cross-border logistics.

Key Features:
- File upload for customs documentation
- PDF/text extraction
- Prompt-based AI audit
- Results displayed in a clear and explainable format
"""

import streamlit as st
import PyPDF2
import os
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Streamlit UI
st.title("🧾 ComplianceBot - Customs Document Checker")
uploaded_file = st.file_uploader("Upload customs document (PDF or TXT)", type=["pdf", "txt"])

if uploaded_file:
    # Extract text from file
    if uploaded_file.name.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        document_text = "
".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    else:
        document_text = uploaded_file.read().decode("utf-8")

    st.text_area("📄 Extracted Document Content", document_text, height=200)

    # Prompt template
    template = PromptTemplate.from_template("""
You are a logistics compliance auditor. Review the following customs declaration and identify:
1. Any missing required fields (e.g., HS Code, consignee name, value, currency, origin).
2. Any inconsistencies or red flags.

Return your findings clearly and suggest any next steps or corrective actions.

Document:
{doc}
""")

    llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    chain = LLMChain(llm=llm, prompt=template)

    if st.button("Run Compliance Audit"):
        result = chain.run(doc=document_text)
        st.markdown("### ✅ ComplianceBot's Audit Summary")
        st.write(result)
