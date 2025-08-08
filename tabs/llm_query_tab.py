# ==============================================================================
# 🤖 AI Query Tab - COMPLETE VERSION with All Functionality
# ==============================================================================
import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Import the necessary functions from the utility files
from utils.llm_utils import get_retriever, answer_question, summarize_manifest
from config import OPENAI_API_KEY

# Predefined sample questions to help users get started
SAMPLE_QUESTIONS = [
    "What is the total number of shipments?",
    "Which carrier has the most shipments?",
    "How many shipments are delayed or pending?",
    "What is the total weight of all shipments?",
    "Which destinations appear most frequently?",
    "What is the average shipping cost?",
    "Are there any high-priority shipments?",
    "Which shipments are scheduled for delivery today?",
    "What is the distribution of shipment statuses?",
    "Which origins have the most outgoing shipments?"
]


def format_docs(docs):
    """
    Combines the page content of a list of LangChain Document objects into a single string.
    This is used to prepare the retrieved documents for the LLM's context.

    Args:
        docs (list): A list of LangChain Document objects.

    Returns:
        str: A single string containing the concatenated content of all documents.
    """
    return "\n\n".join([d.page_content for d in docs])


def initialize_chat_history():
    """Initialize chat history in session state if it doesn't exist."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def add_to_chat_history(question: str, answer: str):
    """Add a question-answer pair to chat history."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.chat_history.append({
        "timestamp": timestamp,
        "question": question,
        "answer": answer
    })


def display_chat_history():
    """Display the chat history in an expandable section."""
    if st.session_state.chat_history:
        with st.expander(f"💬 Chat History ({len(st.session_state.chat_history)} messages)", expanded=False):
            for i, chat in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10
                st.markdown(f"**[{chat['timestamp']}] Q:** {chat['question']}")
                st.markdown(f"**A:** {chat['answer']}")
                if i < len(st.session_state.chat_history[-10:]) - 1:
                    st.markdown("---")


def find_column_case_insensitive(df: pd.DataFrame, target_names: list) -> str:
    """
    Find a column that matches any of the target names (case-insensitive).
    
    Args:
        df: DataFrame to search
        target_names: List of possible column name variations
    
    Returns:
        str or None: Actual column name if found, None otherwise
    """
    df_columns_lower = {col.lower(): col for col in df.columns}
    
    for target in target_names:
        target_lower = target.lower()
        if target_lower in df_columns_lower:
            return df_columns_lower[target_lower]
    
    return None


def get_column_data(df: pd.DataFrame, column_patterns: list):
    """
    Get column data using case-insensitive search.
    
    Args:
        df: DataFrame to search
        column_patterns: List of possible column name patterns
    
    Returns:
        tuple: (column_name, column_data) or (None, None) if not found
    """
    col_name = find_column_case_insensitive(df, column_patterns)
    if col_name:
        return col_name, df[col_name]
    return None, None


def analyze_question_directly(df: pd.DataFrame, question: str) -> str:
    """
    Analyze questions using direct DataFrame operations with case-insensitive column detection.
    FIXED: All formatting and pattern matching issues resolved.
    """
    question_lower = question.lower()
    
    # Define column patterns for case-insensitive search
    status_patterns = ['status', 'shipment_status', 'delivery_status', 'ship_status']
    carrier_patterns = ['carrier', 'carrier_name', 'shipping_company', 'shipper']
    cost_patterns = ['cost', 'price', 'amount', 'shipping_cost', 'total_cost']
    origin_patterns = ['origin', 'from', 'source', 'pickup', 'origin_city']
    destination_patterns = ['destination', 'to', 'dest', 'delivery', 'destination_city']
    shipment_id_patterns = ['shipment_id', 'shipmentid', 'id', 'shipment id', 'tracking', 'reference']
    weight_patterns = ['weight', 'total_weight', 'gross_weight', 'net_weight']
    priority_patterns = ['priority', 'priority_level', 'urgency', 'service_level']
    delivery_date_patterns = ['delivery_date', 'delivery date', 'expected_arrival', 'expected arrival', 'arrival_date']
    
    # Total number of shipments
    if any(phrase in question_lower for phrase in ['total number', 'how many shipments', 'total shipments']):
        if 'delayed' in question_lower or 'pending' in question_lower:
            # Get status column
            status_col, status_data = get_column_data(df, status_patterns)
            shipment_id_col, shipment_id_data = get_column_data(df, shipment_id_patterns)
            
            if status_data is not None:
                # Count delayed and pending shipments (case-insensitive)
                delayed_mask = status_data.str.lower().str.contains('delay', na=False)
                pending_mask = status_data.str.lower().str.contains('pending', na=False)
                
                delayed_count = delayed_mask.sum()
                pending_count = pending_mask.sum()
                
                result = f"**Delayed and Pending Shipments Analysis:**\n\n"
                result += f"• **Delayed shipments:** {delayed_count}\n"
                
                if delayed_count > 0 and shipment_id_data is not None:
                    delayed_ids = shipment_id_data[delayed_mask].tolist()
                    result += f"  - Shipment IDs: {', '.join(map(str, delayed_ids))}\n"
                
                result += f"• **Pending shipments:** {pending_count}\n"
                
                if pending_count > 0 and shipment_id_data is not None:
                    pending_ids = shipment_id_data[pending_mask].tolist()
                    result += f"  - Shipment IDs: {', '.join(map(str, pending_ids))}\n"
                
                result += f"\n**Total delayed + pending:** {delayed_count + pending_count} out of {len(df)} total shipments"
                
                # Show actual status breakdown for context
                result += f"\n\n**Actual Status Breakdown:**\n"
                status_counts = status_data.value_counts()
                for status, count in status_counts.items():
                    result += f"• {status}: {count} shipments\n"
                
                return result
            else:
                return f"Status column not found. Available columns: {', '.join(df.columns)}"
        else:
            return f"**Total shipments:** {len(df)}"
    
    # Carrier analysis
    elif any(phrase in question_lower for phrase in ['carrier has most', 'carrier with most', 'top carrier']):
        carrier_col, carrier_data = get_column_data(df, carrier_patterns)
        
        if carrier_data is not None:
            carrier_counts = carrier_data.value_counts()
            result = f"**Carrier Analysis:**\n\n"
            result += f"🏆 **Top carrier:** {carrier_counts.index[0]} with {carrier_counts.iloc[0]} shipments\n\n"
            result += "**Complete breakdown:**\n"
            for carrier, count in carrier_counts.items():
                percentage = (count / len(df)) * 100
                result += f"• {carrier}: {count} shipments ({percentage:.1f}%)\n"
            return result
        else:
            return f"Carrier column not found. Available columns: {', '.join(df.columns)}"
    
    # FIXED: Status distribution - better pattern matching
    elif any(phrase in question_lower for phrase in [
        'status distribution', 'breakdown', 'status breakdown', 
        'distribution of shipment statuses', 'distribution of status',
        'what is the distribution', 'shipment statuses'
    ]):
        status_col, status_data = get_column_data(df, status_patterns)
        
        if status_data is not None:
            status_counts = status_data.value_counts()
            result = f"**Status Distribution:**\n\n"
            for status, count in status_counts.items():
                percentage = (count / len(df)) * 100
                result += f"• **{status}:** {count} shipments ({percentage:.1f}%)\n"
            result += f"\n**Total shipments:** {len(df)}"
            return result
        else:
            return f"Status column not found. Available columns: {', '.join(df.columns)}"
    
    # FIXED: Cost analysis - proper formatting
    elif any(phrase in question_lower for phrase in [
        'average cost', 'total cost', 'cost analysis', 'shipping cost',
        'average shipping cost', 'what is the average'
    ]):
        cost_col, cost_data = get_column_data(df, cost_patterns)
        
        if cost_data is not None and pd.api.types.is_numeric_dtype(cost_data):
            total_cost = cost_data.sum()
            avg_cost = cost_data.mean()
            min_cost = cost_data.min()
            max_cost = cost_data.max()
            
            result = f"**Cost Analysis:**\n\n"
            result += f"• **Total cost:** ${total_cost:,.2f}\n"
            result += f"• **Average cost:** ${avg_cost:.2f}\n"  # FIXED formatting
            result += f"• **Cost range:** ${min_cost:.2f} - ${max_cost:.2f}\n"
            result += f"• **Number of shipments:** {len(df)}"
            return result
        else:
            return f"Cost column not found or not numeric. Available columns: {', '.join(df.columns)}"
    
    # Origin analysis
    elif any(phrase in question_lower for phrase in ['origins', 'origin', 'outgoing']):
        origin_col, origin_data = get_column_data(df, origin_patterns)
        
        if origin_data is not None:
            origin_counts = origin_data.value_counts()
            result = f"**Origin Analysis:**\n\n"
            result += f"🏆 **Top origin:** {origin_counts.index[0]} with {origin_counts.iloc[0]} shipments\n\n"
            result += "**All origins:**\n"
            for origin, count in origin_counts.items():
                percentage = (count / len(df)) * 100
                result += f"• {origin}: {count} shipments ({percentage:.1f}%)\n"
            return result
        else:
            return f"Origin column not found. Available columns: {', '.join(df.columns)}"
    
    # Destination analysis
    elif any(phrase in question_lower for phrase in ['destination', 'popular destination']):
        dest_col, dest_data = get_column_data(df, destination_patterns)
        
        if dest_data is not None:
            dest_counts = dest_data.value_counts()
            result = f"**Destination Analysis:**\n\n"
            result += f"🏆 **Top destination:** {dest_counts.index[0]} with {dest_counts.iloc[0]} shipments\n\n"
            result += "**All destinations:**\n"
            for dest, count in dest_counts.items():
                percentage = (count / len(df)) * 100
                result += f"• {dest}: {count} shipments ({percentage:.1f}%)\n"
            return result
        else:
            return f"Destination column not found. Available columns: {', '.join(df.columns)}"
    
    # Weight analysis
    elif 'weight' in question_lower:
        weight_col, weight_data = get_column_data(df, weight_patterns)
        
        if weight_data is not None and pd.api.types.is_numeric_dtype(weight_data):
            total_weight = weight_data.sum()
            avg_weight = weight_data.mean()
            return f"**Weight Analysis:**\n\n• **Total weight:** {total_weight:,.2f}\n• **Average weight:** {avg_weight:.2f}"
        else:
            return f"Weight column not found or not numeric. Available columns: {', '.join(df.columns)}"
    
    # FIXED: Priority analysis - show actual shipment IDs
    elif any(phrase in question_lower for phrase in [
        'priority', 'high priority', 'high-priority', 'are there any high'
    ]):
        priority_col, priority_data = get_column_data(df, priority_patterns)
        shipment_id_col, shipment_id_data = get_column_data(df, shipment_id_patterns)
        
        if priority_data is not None:
            high_priority_mask = priority_data.str.lower().str.contains('high', na=False)
            high_priority_count = high_priority_mask.sum()
            
            result = f"**High Priority Shipments:** {high_priority_count} out of {len(df)} total shipments\n\n"
            
            if high_priority_count > 0:
                if shipment_id_data is not None:
                    high_priority_ids = shipment_id_data[high_priority_mask].tolist()
                    result += f"**High Priority Shipment IDs:**\n"
                    for ship_id in high_priority_ids:
                        result += f"• {ship_id}\n"
                else:
                    result += "Shipment ID column not found to list specific shipments."
            
            return result
        else:
            return f"Priority column not found. Available columns: {', '.join(df.columns)}"
    
    # NEW: Delivery today analysis
    elif any(phrase in question_lower for phrase in [
        'delivery today', 'scheduled for delivery today', 'delivering today',
        'scheduled today', 'today delivery'
    ]):
        delivery_date_col, delivery_date_data = get_column_data(df, delivery_date_patterns)
        shipment_id_col, shipment_id_data = get_column_data(df, shipment_id_patterns)
        
        if delivery_date_data is not None:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            today_alt = datetime.now().strftime('%m/%d/%Y')
            today_alt2 = datetime.now().strftime('%d/%m/%Y')
            
            # Check multiple date formats
            today_mask = (
                delivery_date_data.astype(str).str.contains(today, na=False) |
                delivery_date_data.astype(str).str.contains(today_alt, na=False) |
                delivery_date_data.astype(str).str.contains(today_alt2, na=False) |
                delivery_date_data.astype(str).str.lower().str.contains('today', na=False)
            )
            
            today_count = today_mask.sum()
            
            result = f"**Shipments Scheduled for Delivery Today:** {today_count} out of {len(df)} total shipments\n\n"
            
            if today_count > 0:
                if shipment_id_data is not None:
                    today_ids = shipment_id_data[today_mask].tolist()
                    result += f"**Today's Deliveries:**\n"
                    for ship_id in today_ids:
                        result += f"• {ship_id}\n"
                else:
                    result += "Shipment ID column not found to list specific shipments."
            else:
                result += f"**Today's date:** {today}\n"
                result += "No shipments scheduled for delivery today."
            
            return result
        else:
            return f"Delivery date column not found. Available columns: {', '.join(df.columns)}"
    
    # Fallback - return None to use LLM
    return None


def show_llm_query_tab(df: pd.DataFrame):
    """
    Displays the AI Query tab, allowing users to ask natural language questions
    about the manifest data with enhanced features and case-insensitive analysis.
    """
    st.header("🤖 AI Insights")
    st.write("Ask LogiBot natural language questions about your manifest data.")

    # Initialize chat history
    initialize_chat_history()

    # Check if a DataFrame has been uploaded and processed
    if df is None or df.empty:
        st.info("ℹ️ Please upload a manifest file to ask questions.")
        return

    # Create columns for layout
    col1, col2 = st.columns([2, 1])

    with col1:
        # Main query interface
        st.subheader("💭 Ask Your Question")
        
        # Question input options
        input_method = st.radio(
            "Choose input method:",
            ["Type your question", "Select from examples"],
            horizontal=True,
            key="input_method"
        )

        if input_method == "Type your question":
            question = st.text_area(
                "Enter your question:",
                placeholder="e.g., 'What are the total number of delayed shipments?' or 'Which carrier has the most shipments?'",
                height=100,
                key="user_question"
            )
        else:
            question = st.selectbox(
                "Choose an example question:",
                [""] + SAMPLE_QUESTIONS,
                key="example_question"
            )

    with col2:
        # Quick stats about the data
        st.subheader("📊 Data Overview")
        
        # Basic statistics
        stats_data = {
            "Total Rows": len(df),
            "Columns": len(df.columns),
            "Memory Usage": f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB"
        }
        
        for key, value in stats_data.items():
            st.metric(key, value)

        # Show actual status breakdown for reference (case-insensitive)
        status_col, status_data = get_column_data(df, ['status', 'shipment_status', 'delivery_status'])
        if status_data is not None:
            status_counts = status_data.value_counts()
            with st.expander("📈 Status Breakdown"):
                for status, count in status_counts.items():
                    st.write(f"• {status}: {count}")

        # Column information
        with st.expander("📋 Available Columns"):
            for col in df.columns:
                unique_count = df[col].nunique()
                null_count = df[col].isnull().sum()
                st.write(f"**{col}**: {unique_count} unique, {null_count} nulls")

    # Query buttons
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        ask_button = st.button("🚀 Get Answer", type="primary", use_container_width=True)
    
    with col_btn2:
        summarize_button = st.button("📄 Generate Summary", use_container_width=True)
    
    with col_btn3:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)

    # Handle button clicks
    if clear_button:
        st.session_state.chat_history = []
        if hasattr(st.session_state, 'llm_answer'):
            st.session_state.llm_answer = None
        if hasattr(st.session_state, 'latest_answer'):
            st.session_state.latest_answer = None
        st.success("🗑️ Chat history cleared!")
        st.rerun()

    if summarize_button:
        if "ai_summary" not in st.session_state or st.session_state.ai_summary == "No AI summary has been generated yet.":
            with st.spinner("📝 Generating comprehensive summary..."):
                try:
                    summary = summarize_manifest(df, openai_api_key=OPENAI_API_KEY)
                    st.session_state.ai_summary = summary
                    add_to_chat_history("Generate a summary of the manifest", summary)
                    st.success("✅ Summary generated!")
                except Exception as e:
                    st.error(f"❌ Error generating summary: {e}")
        else:
            st.info("ℹ️ Summary already generated. Check the answer below.")

    if ask_button and question.strip():
        with st.spinner("🤔 Analyzing your question..."):
            try:
                # First try direct analysis for accuracy
                direct_answer = analyze_question_directly(df, question)
                
                if direct_answer:
                    # Use direct analysis result (100% accurate)
                    answer = direct_answer
                    st.info("✅ Using direct data analysis for maximum accuracy...")
                else:
                    # Initialize retriever if needed
                    if "retriever" not in st.session_state:
                        with st.spinner("🧠 Initializing AI components..."):
                            retriever_result = get_retriever(df, OPENAI_API_KEY)
                            
                            if isinstance(retriever_result, tuple):
                                st.session_state.retriever, st.session_state.df_for_llm = retriever_result
                            else:
                                st.session_state.retriever = retriever_result
                    
                    # Use LLM for complex questions
                    answer = answer_question(
                        st.session_state.retriever,
                        question,
                        OPENAI_API_KEY
                    )
                    st.info("🤖 Using AI analysis...")
                
                # Add to chat history
                add_to_chat_history(question, answer)
                
                # Store the latest answer
                st.session_state.latest_answer = answer
                st.session_state.llm_answer = answer
                
            except Exception as e:
                st.error(f"❌ An error occurred while generating the answer: {e}")
                st.session_state.latest_answer = None

    elif ask_button and not question.strip():
        st.warning("⚠️ Please enter a question.")

    # Display results
    st.markdown("---")
    
    # Show latest answer prominently
    if hasattr(st.session_state, 'latest_answer') and st.session_state.latest_answer:
        st.subheader("🤖 LogiBot's Latest Answer:")
        st.markdown(st.session_state.latest_answer)
    
    # Show AI summary if available
    elif "ai_summary" in st.session_state and st.session_state.ai_summary != "No AI summary has been generated yet.":
        st.subheader("📄 Manifest Summary:")
        st.info(st.session_state.ai_summary)

    # Display chat history
    display_chat_history()

    # Tips and help section
    with st.expander("💡 Tips for Better Questions", expanded=False):
        st.markdown("""
        **Examples of good questions:**
        - "How many shipments are from each carrier?"
        - "What's the average delivery time?"
        - "Which shipments are high priority?"
        - "Show me shipments going to California"
        - "What's the total cost of all shipments?"
        
        **Tips for better results:**
        - Be specific about what you want to know
        - Mention column names if you know them
        - Ask one question at a time
        - Use natural language - no need for SQL syntax
        """)

    # Export chat history option
    if st.session_state.chat_history:
        st.markdown("---")
        if st.button("📥 Export Chat History"):
            chat_df = pd.DataFrame(st.session_state.chat_history)
            csv = chat_df.to_csv(index=False)
            st.download_button(
                "Download Chat History as CSV",
                csv,
                file_name=f"logibot_chat_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

    # Data preview
    if st.checkbox("📋 Show Data Preview"):
        st.subheader("Data Sample")
        st.dataframe(df.head(10), use_container_width=True)