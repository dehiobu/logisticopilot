# LogistiCopilot: AI Agent Portal for Logistics

This project demonstrates a working prototype of AI agents designed for the logistics industry. It features document summarisation, compliance checks, and data-driven insights using LangChain + Streamlit.

s

LogiBot is a modular AI-powered Streamlit app that helps logistics teams understand and optimise their shipment manifests using LLMs like GPT-3.5. It provides manifest summarisation, compliance checks, interactive Q&A, and export options.

---

## 🚀 Features

- 📋 **Manifest Upload & AI Summary** – Instantly summarise logistics data
- 💬 **Manifest Q&A** – Ask the AI questions like “Which shipments are delayed?”
- ✅ **Compliance Checker** – Flags missing tracking IDs, unapproved carriers, and more
- 📧 **Email Alerts** – Sends alerts to stakeholders
- 📊 **Dashboard Metrics** – Shipment KPIs and charts
- 📤 **Export** – Download full report as Excel or PDF

---

## 🧱 Project Structure
logisticopilot/
├── app.py
├── config.py
├── data/
│ ├── approved_carriers.csv
│ └── sample_logistics_manifest.csv
├── utils/
│ ├── pdf_utils.py
│ ├── email_utils.py
│ ├── carrier_utils.py
│ ├── llm_utils.py
│ ├── excel_utils.py
│ ├── compliance_utils.py
│ └── dashboard_utils.py
└── README.md

---

## 💻 Tech Stack

- **Streamlit** – Frontend UI framework
- **LangChain** – LLM chaining and prompt logic
- **OpenAI / Azure OpenAI** – LLM inference via API key
- **Pandas** – Manifest parsing and transformation
- **Matplotlib** – Charts and KPI visualisation
- **FPDF** – PDF summary exports
- **openpyxl** – Excel export engine
- **SMTP / smtplib** – Email notifications

---

## 📦 Installation

```bash
pip install -r requirements.txt
