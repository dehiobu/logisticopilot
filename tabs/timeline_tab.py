# ======================================================
# tabs/timeline_tab.py
# This module contains the function to display the
# shipment timeline dashboard tab.
# ======================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

def find_column_flexible(df, patterns):
    """
    Find a column that matches any of the given patterns (case-insensitive, space-flexible).
    """
    for col in df.columns:
        col_clean = col.lower().replace(' ', '').replace('_', '').replace('-', '')
        for pattern in patterns:
            pattern_clean = pattern.lower().replace(' ', '').replace('_', '').replace('-', '')
            if pattern_clean in col_clean:
                return col
    return None

def show_timeline_tab(df: pd.DataFrame):
    """
    Displays the shipment timeline visualization tab.
    
    Args:
        df (pd.DataFrame): The manifest data from the uploaded file.
    """
    st.header("⏳ Shipment Timeline")
    st.write("Visualize the timeline of your shipments by their expected arrival dates.")

    if df is None or df.empty:
        st.info("Please upload a manifest file to view the shipment timeline.")
        return

    # Debug: Show available columns
    st.write("🔍 **Available Columns:**")
    st.write(list(df.columns))

    # Flexible column detection
    shipment_id_col = find_column_flexible(df, ['shipment id', 'shipmentid', 'id', 'shipment'])
    departure_col = find_column_flexible(df, ['departure date', 'departuredate', 'ship date', 'start date'])
    arrival_col = find_column_flexible(df, ['expected arrival', 'expectedarrival', 'arrival date', 'delivery date', 'due date'])

    st.write(f"**Detected Columns:**")
    st.write(f"• Shipment ID: {shipment_id_col}")
    st.write(f"• Departure Date: {departure_col}")
    st.write(f"• Expected Arrival: {arrival_col}")

    # Check if the required columns exist
    if not departure_col or not arrival_col:
        st.warning(
            "⚠️ The manifest data does not contain the required date columns. "
            "Looking for 'Departure Date' and 'Expected Arrival' (or similar)."
        )
        
        # Show potential date columns
        potential_date_cols = []
        for col in df.columns:
            if any(word in col.lower() for word in ['date', 'departure', 'arrival', 'delivery', 'expected', 'due']):
                potential_date_cols.append(col)
        
        if potential_date_cols:
            st.write("**Potential date columns found:**")
            for col in potential_date_cols:
                st.write(f"• {col} - Sample: {df[col].head(2).tolist()}")
        return
    
    # Create a new DataFrame for the Gantt chart to avoid modifying the original
    gantt_df = df.copy()
    
    # Use shipment ID column or create index-based IDs
    if shipment_id_col:
        y_column = shipment_id_col
    else:
        gantt_df['Shipment_Index'] = gantt_df.index + 1
        y_column = 'Shipment_Index'
        st.info("No Shipment ID column found. Using row numbers for display.")
    
    # Ensure the date columns are in datetime format for plotting
    try:
        gantt_df['Departure_Parsed'] = pd.to_datetime(gantt_df[departure_col], dayfirst=True, errors='coerce')
        gantt_df['Arrival_Parsed'] = pd.to_datetime(gantt_df[arrival_col], dayfirst=True, errors='coerce')
        
        # Check for parsing errors and show problematic data
        departure_na = gantt_df['Departure_Parsed'].isna()
        arrival_na = gantt_df['Arrival_Parsed'].isna()
        
        departure_na_count = departure_na.sum()
        arrival_na_count = arrival_na.sum()
        
        if departure_na_count > 0:
            st.warning(f"⚠️ Could not parse {departure_na_count} departure dates")
            st.write("**Problematic departure dates:**")
            problematic_departures = gantt_df[departure_na][departure_col].tolist()
            for i, val in enumerate(problematic_departures):
                st.write(f"  Row {gantt_df[departure_na].index[i]}: '{val}'")
                
        if arrival_na_count > 0:
            st.warning(f"⚠️ Could not parse {arrival_na_count} arrival dates")
            st.write("**Problematic arrival dates:**")
            problematic_arrivals = gantt_df[arrival_na][arrival_col].tolist()
            for i, val in enumerate(problematic_arrivals):
                st.write(f"  Row {gantt_df[arrival_na].index[i]}: '{val}'")
        
        # Show sample parsed dates
        st.write(f"**Sample successfully parsed dates:**")
        valid_departures = gantt_df['Departure_Parsed'].dropna()
        valid_arrivals = gantt_df['Arrival_Parsed'].dropna()
        
        if len(valid_departures) > 0:
            st.write(f"• Departure: {valid_departures.head(2).dt.strftime('%Y-%m-%d').tolist()}")
        if len(valid_arrivals) > 0:
            st.write(f"• Arrival: {valid_arrivals.head(2).dt.strftime('%Y-%m-%d').tolist()}")
            
    except Exception as e:
        st.error(f"❌ Error parsing date columns: {e}")
        st.info("Please ensure the date format is correct (e.g., YYYY-MM-DD, DD/MM/YYYY, etc.)")
        return

    # Filter out rows with invalid dates
    valid_rows = gantt_df['Departure_Parsed'].notna() & gantt_df['Arrival_Parsed'].notna()
    gantt_df_clean = gantt_df[valid_rows].copy()
    
    if len(gantt_df_clean) == 0:
        st.error("❌ No valid date ranges found. Please check your date formats.")
        return
    
    st.success(f"✅ Found {len(gantt_df_clean)} shipments with valid dates")

    # Determine color column (Status if available)
    color_col = find_column_flexible(df, ['status', 'state', 'condition'])
    
    # Create the Gantt chart using Plotly Express
    if color_col:
        fig = px.timeline(
            gantt_df_clean,
            x_start="Departure_Parsed",
            x_end="Arrival_Parsed",
            y=y_column,
            color=color_col,
            title="📅 Shipment Timeline",
            height=max(400, len(gantt_df_clean) * 30),
            hover_data=[departure_col, arrival_col] if departure_col != arrival_col else [departure_col]
        )
    else:
        fig = px.timeline(
            gantt_df_clean,
            x_start="Departure_Parsed",
            x_end="Arrival_Parsed",
            y=y_column,
            title="📅 Shipment Timeline",
            height=max(400, len(gantt_df_clean) * 30),
            hover_data=[departure_col, arrival_col] if departure_col != arrival_col else [departure_col]
        )

    # Customize the layout for better readability
    fig.update_yaxes(categoryorder='total ascending')
    fig.update_layout(
        xaxis_title="Timeline",
        yaxis_title="Shipments",
        hovermode="closest",
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        font=dict(size=12)
    )
    
    # Format x-axis to show dates nicely
    fig.update_xaxes(
        tickformat="%Y-%m-%d",
        tickangle=45
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Timeline Analytics
    st.markdown("---")
    st.subheader("📊 Timeline Analytics")
    
    # Calculate durations
    gantt_df_clean['Duration_Days'] = (gantt_df_clean['Arrival_Parsed'] - gantt_df_clean['Departure_Parsed']).dt.days
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_duration = gantt_df_clean['Duration_Days'].mean()
        st.metric("Average Transit Time", f"{avg_duration:.1f} days")
    
    with col2:
        min_duration = gantt_df_clean['Duration_Days'].min()
        st.metric("Shortest Transit", f"{min_duration} days")
    
    with col3:
        max_duration = gantt_df_clean['Duration_Days'].max()
        st.metric("Longest Transit", f"{max_duration} days")
    
    with col4:
        total_shipments = len(gantt_df_clean)
        st.metric("Valid Shipments", total_shipments)
    
    # Show detailed timeline data
    st.markdown("---")
    st.subheader("📋 Timeline Details")
    
    display_cols = []
    if y_column:
        display_cols.append(y_column)
    if departure_col:
        display_cols.append(departure_col)
    if arrival_col:
        display_cols.append(arrival_col)
    display_cols.append('Duration_Days')
    if color_col:
        display_cols.append(color_col)
    
    # Filter to only show columns that exist
    display_cols = [col for col in display_cols if col in gantt_df_clean.columns]
    
    # Sort by the original departure column (not the parsed one)
    if departure_col in gantt_df_clean.columns:
        try:
            st.dataframe(
                gantt_df_clean[display_cols].sort_values(departure_col),
                use_container_width=True
            )
        except:
            # Fallback: don't sort if there's any issue
            st.dataframe(
                gantt_df_clean[display_cols],
                use_container_width=True
            )
    else:
        st.dataframe(
            gantt_df_clean[display_cols],
            use_container_width=True
        )