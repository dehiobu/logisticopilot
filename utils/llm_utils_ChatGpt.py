import streamlit as st
import pandas as pd
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import DataFrameLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate

# A simple document formatting utility for printing to Streamlit.
def format_docs(docs: list[Document]) -> str:
    """
    Combines the page content of a list of LangChain Document objects into a single string.

    Args:
        docs (list[Document]): A list of LangChain Document objects.

    Returns:
        str: A single string containing the concatenated content of all documents.
    """
    return "\n\n".join(doc.page_content for doc in docs)

@st.cache_data
def get_retriever(df: pd.DataFrame) -> FAISS:
    """
    Creates a FAISS vector store from a DataFrame and returns a retriever.

    Args:
        df (pd.DataFrame): The input manifest DataFrame.

    Returns:
        FAISS: A FAISS vector store configured for retrieval.
    """
    st.info("Creating a vector store from the manifest data...")

    # Load the manifest data into LangChain Documents
    loader = DataFrameLoader(df)
    documents = loader.load()

    # Split the documents into chunks suitable for embeddings
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    # Generate OpenAI embeddings and build FAISS vector index
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)

    st.success("Vector store created successfully.")
    return vectorstore

def answer_question(documents: list[Document], question: str, api_key: str) -> str:
    """
    Answers a question about the manifest data using a LangChain RAG pipeline.

    Args:
        documents (list[Document]): The manifest data as a list of LangChain Document objects.
        question (str): The user's question about the data.
        api_key (str): The OpenAI API key.

    Returns:
        str: The AI-generated answer.
    """
    st.info("Thinking about the data...")

    # Initialise the LLM and embeddings model
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)

    # Create a retriever from the FAISS vector store
    vectorstore = FAISS.from_documents(documents, embeddings)
    retriever = vectorstore.as_retriever()

    # Define a prompt template that expects {context} and {input}
    prompt = PromptTemplate.from_template(
        """
        You are a helpful AI assistant for a logistics company.
        Use the following context to answer the question below.

        Context:
        {context}

        Question:
        {input}
        """
    )

    # Build a chain that combines the retrieved documents with the prompt
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Connect retriever to the document chain
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    # Send only the question as 'input'; context will be auto-retrieved
    response = retrieval_chain.invoke({"input": question})
    return response["answer"]

def summarize_manifest(df: pd.DataFrame, api_key: str) -> str:
    """
    Generates a summary of the manifest data using an LLM.

    Args:
        df (pd.DataFrame): The input manifest DataFrame.
        api_key (str): The OpenAI API key.

    Returns:
        str: A summary of the manifest.
    """
    st.info("Generating an AI summary of the manifest...")

    # Initialise the language model
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)

    # Convert the DataFrame into plain text
    manifest_string = df.to_string(index=False)

    # Prompt the LLM to summarise the manifest data
    prompt = f"""
    You are an AI assistant for a logistics company.
    Analyze the following manifest data and provide a concise summary, highlighting
    key metrics like total shipments, number of unique carriers, and any delayed shipments.

    Manifest data:
    {manifest_string}

    Summary:
    """

    response = llm.invoke(prompt)
    return response.content
