# ai_documentation_tab.py
import streamlit as st

def show_ai_documentation_tab():
    """
    Displays content for the AI Documentation tab, including useful links.
    The links have been updated to point to real documentation for the
    libraries used in the application.
    """
    st.title("📚 AI Copilot Documentation")
    st.write(
        "Here you can find useful resources to help you get the most out of LogiBot. "
        "The application is built using Streamlit and LangChain, so these docs "
        "will be highly relevant."
    )

    st.markdown("---")
    
    # Updated to use real, working documentation links.
    st.markdown("📘 [Streamlit Documentation](https://docs.streamlit.io/)")
    st.markdown("🔗 [LangChain Python API Reference](https://python.langchain.com/api_reference/)")

    st.info("These links now point to the official documentation for the frameworks used to build this app.")
