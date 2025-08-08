# ==============================================================================
# 🧠 LLM Utilities - DIRECT DATA ACCESS VERSION
# ==============================================================================
import streamlit as st
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema import StrOutputParser
import os
import json


def is_statistical_query(question: str) -> bool:
    """
    Determine if a question is asking for statistics that can be answered directly from data.
    
    Args:
        question (str): User's question
        
    Returns:
        bool: True if it's a statistical/counting query
    """
    statistical_keywords = [
        'how many', 'count', 'total', 'number of', 'which carrier has most',
        'top carrier', 'most shipments', 'breakdown', 'distribution',
        'delayed', 'status', 'sum', 'average', 'percentage', 'ratio'
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in statistical_keywords)


def analyze_data_directly(df: pd.DataFrame, question: str) -> dict:
    """
    Directly analyze the DataFrame to get accurate statistics.
    
    Args:
        df (pd.DataFrame): The manifest DataFrame
        question (str): User's question
        
    Returns:
        dict: Analysis results
    """
    results = {}
    question_lower = question.lower()
    
    # Basic statistics
    results['total_shipments'] = len(df)
    results['total_columns'] = len(df.columns)
    results['columns'] = list(df.columns)
    
    # Carrier analysis
    if 'Carrier' in df.columns:
        carrier_counts = df['Carrier'].value_counts()
        results['carrier_breakdown'] = carrier_counts.to_dict()
        results['unique_carriers'] = len(carrier_counts)
        results['top_carrier'] = carrier_counts.index[0] if len(carrier_counts) > 0 else None
        results['top_carrier_count'] = carrier_counts.iloc[0] if len(carrier_counts) > 0 else 0
    
    # Status analysis
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts()
        results['status_breakdown'] = status_counts.to_dict()
        results['unique_statuses'] = len(status_counts)
        
        # Count delayed shipments
        delayed_mask = df['Status'].str.lower().str.contains('delay', na=False)
        results['delayed_shipments'] = delayed_mask.sum()
        results['delayed_shipment_ids'] = df[delayed_mask]['Shipment ID'].tolist() if 'Shipment ID' in df.columns else []
    
    # Cost analysis
    if 'Cost' in df.columns and pd.api.types.is_numeric_dtype(df['Cost']):
        results['total_cost'] = df['Cost'].sum()
        results['average_cost'] = df['Cost'].mean()
        results['min_cost'] = df['Cost'].min()
        results['max_cost'] = df['Cost'].max()
    
    # Origin analysis
    if 'Origin' in df.columns:
        origin_counts = df['Origin'].value_counts()
        results['origin_breakdown'] = origin_counts.to_dict()
        results['most_common_origin'] = origin_counts.index[0] if len(origin_counts) > 0 else None
    
    # Destination analysis
    if 'Destination' in df.columns:
        dest_counts = df['Destination'].value_counts()
        results['destination_breakdown'] = dest_counts.to_dict()
        results['most_common_destination'] = dest_counts.index[0] if len(dest_counts) > 0 else None
    
    return results


def get_direct_data_context(df: pd.DataFrame) -> str:
    """
    Create a comprehensive data context string with all the statistics.
    
    Args:
        df (pd.DataFrame): The manifest DataFrame
        
    Returns:
        str: Formatted context string
    """
    analysis = analyze_data_directly(df, "comprehensive analysis")
    
    context = f"""
COMPLETE LOGISTICS MANIFEST ANALYSIS:

BASIC INFORMATION:
- Total Shipments: {analysis['total_shipments']}
- Total Columns: {analysis['total_columns']}
- Column Names: {', '.join(analysis['columns'])}

"""
    
    # Add carrier breakdown
    if 'carrier_breakdown' in analysis:
        context += "CARRIER BREAKDOWN:\n"
        for carrier, count in analysis['carrier_breakdown'].items():
            context += f"- {carrier}: {count} shipments\n"
        context += f"- Top Carrier: {analysis['top_carrier']} ({analysis['top_carrier_count']} shipments)\n\n"
    
    # Add status breakdown
    if 'status_breakdown' in analysis:
        context += "STATUS BREAKDOWN:\n"
        for status, count in analysis['status_breakdown'].items():
            context += f"- {status}: {count} shipments\n"
        if analysis.get('delayed_shipments', 0) > 0:
            context += f"- Delayed Shipments: {analysis['delayed_shipments']}\n"
            context += f"- Delayed Shipment IDs: {', '.join(analysis['delayed_shipment_ids'])}\n"
        context += "\n"
    
    # Add cost information
    if 'total_cost' in analysis:
        context += f"COST ANALYSIS:\n"
        context += f"- Total Cost: ${analysis['total_cost']:.2f}\n"
        context += f"- Average Cost: ${analysis['average_cost']:.2f}\n"
        context += f"- Min Cost: ${analysis['min_cost']:.2f}\n"
        context += f"- Max Cost: ${analysis['max_cost']:.2f}\n\n"
    
    # Add origin/destination info
    if 'origin_breakdown' in analysis:
        context += "ORIGIN ANALYSIS:\n"
        for origin, count in list(analysis['origin_breakdown'].items())[:5]:  # Top 5
            context += f"- {origin}: {count} shipments\n"
        context += "\n"
    
    if 'destination_breakdown' in analysis:
        context += "DESTINATION ANALYSIS:\n"
        for dest, count in list(analysis['destination_breakdown'].items())[:5]:  # Top 5
            context += f"- {dest}: {count} shipments\n"
        context += "\n"
    
    # Add raw data sample
    context += "SAMPLE DATA (First 5 rows):\n"
    context += df.head().to_string(index=False)
    
    return context


@st.cache_resource
def get_retriever(df: pd.DataFrame, openai_api_key: str):
    """
    For backward compatibility - returns the DataFrame for direct access.
    """
    st.info("Setting up direct data access (no vector store needed)...")
    return df  # Return DataFrame directly instead of retriever


def summarize_manifest(df: pd.DataFrame, openai_api_key: str):
    """
    Generates a summary using direct data analysis (no vector store).
    """
    st.info("Generating a summary of your manifest...")
    os.environ["OPENAI_API_KEY"] = openai_api_key

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_api_key)

    # Get direct analysis
    context = get_direct_data_context(df)

    prompt = PromptTemplate.from_template(
        """
        You are an experienced logistics assistant. Based on the comprehensive data analysis below, 
        provide a clear, accurate summary focusing on key metrics and insights.

        IMPORTANT: Use the EXACT numbers provided in the analysis. Do not estimate or approximate.

        Data Analysis:
        {context}

        Provide a concise summary highlighting:
        1. Total shipments and key metrics
        2. Carrier distribution and top performers  
        3. Status breakdown and any issues
        4. Cost analysis if available
        5. Any notable patterns or concerns

        Summary:
        """
    )

    summarize_chain = prompt | llm | StrOutputParser()
    response = summarize_chain.invoke({"context": context})
    
    return response


def answer_question(df_or_retriever, question: str, openai_api_key: str) -> str:
    """
    Answer questions using direct data analysis for statistical queries,
    or fallback to text-based analysis for other queries.
    """
    st.info("Analyzing your question...")
    os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Handle both DataFrame (new) and retriever (old) for backward compatibility
    if isinstance(df_or_retriever, pd.DataFrame):
        df = df_or_retriever
    else:
        # This shouldn't happen with the new system, but handle gracefully
        st.warning("Using fallback mode - results may be less accurate")
        return "I need the DataFrame to provide accurate answers. Please reload your data."
    
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_api_key)

    # For statistical queries, use direct data analysis
    if is_statistical_query(question):
        st.info("Using direct data analysis for maximum accuracy...")
        
        # Get comprehensive data context
        context = get_direct_data_context(df)
        
        # Also get specific analysis for the question
        specific_analysis = analyze_data_directly(df, question)
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a logistics data analyst. Answer the question using the provided data analysis.
            
            CRITICAL: Use ONLY the exact numbers and facts from the analysis below. Do not estimate or guess.
            
            Question: {question}
            
            Complete Data Analysis:
            {context}
            
            Specific Analysis Results:
            {specific_analysis}
            
            Provide a direct, factual answer using the exact data provided:
            """
        )
        
        response = llm.invoke(
            prompt.format_messages(
                question=question,
                context=context,
                specific_analysis=json.dumps(specific_analysis, indent=2)
            )
        )
        
        return response.content
    
    else:
        # For non-statistical queries, use the full context
        context = get_direct_data_context(df)
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a helpful logistics assistant. Answer the question based on the manifest data provided.
            
            Question: {question}
            
            Manifest Data and Analysis:
            {context}
            
            Answer:
            """
        )
        
        response = llm.invoke(
            prompt.format_messages(
                question=question,
                context=context
            )
        )
        
        return response.content


def get_data_overview(df: pd.DataFrame) -> dict:
    """
    Get a quick data overview for the UI.
    
    Args:
        df (pd.DataFrame): The manifest DataFrame
        
    Returns:
        dict: Overview statistics
    """
    analysis = analyze_data_directly(df, "overview")
    
    overview = {
        'total_rows': analysis['total_shipments'],
        'total_columns': analysis['total_columns'],
        'columns': analysis['columns']
    }
    
    if 'unique_carriers' in analysis:
        overview['unique_carriers'] = analysis['unique_carriers']
        overview['top_carrier'] = analysis['top_carrier']
    
    if 'unique_statuses' in analysis:
        overview['unique_statuses'] = analysis['unique_statuses']
    
    if 'delayed_shipments' in analysis:
        overview['delayed_shipments'] = analysis['delayed_shipments']
    
    return overview