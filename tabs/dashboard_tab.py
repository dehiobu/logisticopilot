import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.column_utils import (
    ColumnMapper, 
    detect_column_mapping, 
    validate_required_columns,
    get_column_info
)  # Add this import


def show_dashboard_tab(df: pd.DataFrame):
    """
    Displays an interactive dashboard with key metrics and visualizations of the manifest data.
    Now uses ColumnMapper for robust column handling and consistent display names.
    
    Args:
        df (pd.DataFrame): The normalized manifest data from the uploaded file.
    """
    st.header("📊 Dashboard")
    st.write("An overview of your manifest data.")

    if df is None or df.empty:
        st.info("Please upload a manifest file to view the dashboard.")
        return

    # Show available columns with display names
    display_columns = [ColumnMapper.get_display_name(col) for col in df.columns]
    st.info(f"📋 **Loaded columns:** {', '.join(display_columns)}")

    # --- Key Metrics ---
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    total_shipments = len(df)
    
    # Use ColumnMapper instead of manual checking
    carrier_col = ColumnMapper.get_column_if_exists(df, 'carrier')
    status_col = ColumnMapper.get_column_if_exists(df, 'status')
    
    total_carriers = df[carrier_col].nunique() if carrier_col else 0
    delayed_shipments = df[df[status_col].str.lower().str.contains('delayed', na=False)].shape[0] if status_col else 0
    in_transit_shipments = df[df[status_col].str.lower().str.contains('in transit', na=False)].shape[0] if status_col else 0

    with col1:
        st.metric("Total Shipments", total_shipments)
    with col2:
        st.metric("Total Carriers", total_carriers)
    with col3:
        st.metric("Delayed Shipments", delayed_shipments)
    with col4:
        st.metric("In Transit", in_transit_shipments)

    # --- Data Preview with Display Names ---
    st.subheader("📋 Data Preview")
    display_df = df.copy()
    display_columns_mapping = {col: ColumnMapper.get_display_name(col) for col in df.columns}
    display_df = display_df.rename(columns=display_columns_mapping)
    st.dataframe(display_df.head(10), use_container_width=True)

    # --- Visualizations ---
    st.markdown("### Visualizations")

    # Status Distribution - Updated to use display names
    if status_col:
        st.subheader("Shipment Status Distribution")
        status_counts = df[status_col].value_counts().reset_index()
        status_counts.columns = [ColumnMapper.get_display_name('status'), 'Count']
        fig_status = px.pie(
            status_counts,
            names=ColumnMapper.get_display_name('status'),
            values='Count',
            title='Distribution of Shipment Statuses',
            hole=0.3
        )
        st.plotly_chart(fig_status, use_container_width=True)

    # Carriers by Shipment Count - Updated to use display names
    if carrier_col:
        st.subheader("Shipments by Carrier")
        carrier_counts = df[carrier_col].value_counts().reset_index()
        carrier_counts.columns = [ColumnMapper.get_display_name('carrier'), 'Count']
        fig_carriers = px.bar(
            carrier_counts,
            x=ColumnMapper.get_display_name('carrier'),
            y='Count',
            title='Number of Shipments per Carrier'
        )
        st.plotly_chart(fig_carriers, use_container_width=True)

    # --- Geo-Spatial Visualization - Updated to use ColumnMapper ---
    # Check for geographic columns using ColumnMapper
    origin_col = ColumnMapper.get_column_if_exists(df, 'origin')
    destination_col = ColumnMapper.get_column_if_exists(df, 'destination')
    
    # For lat/lon, we'll check for common variations
    origin_lat_col = None
    origin_lon_col = None
    dest_lat_col = None
    dest_lon_col = None
    
    # Check for various lat/lon column patterns
    for col in df.columns:
        col_lower = col.lower()
        if 'origin' in col_lower and 'lat' in col_lower:
            origin_lat_col = col
        elif 'origin' in col_lower and 'lon' in col_lower:
            origin_lon_col = col
        elif 'dest' in col_lower and 'lat' in col_lower:
            dest_lat_col = col
        elif 'dest' in col_lower and 'lon' in col_lower: 
            dest_lon_col = col

    required_geo_columns = [origin_col, destination_col, origin_lat_col, origin_lon_col, dest_lat_col, dest_lon_col]
    missing_geo_data = any(col is None for col in required_geo_columns)

    if not missing_geo_data:
        st.subheader("Shipment Routes Map")
        st.write("Visualizing shipment routes from origin to destination.")

        fig_map = go.Figure()
        
        # Add a light, neutral-colored background map
        fig_map.add_trace(go.Scattergeo(
            locationmode = 'USA-states',
            lon = df[origin_lon_col],
            lat = df[origin_lat_col],
            hoverinfo = 'text',
            text = df[origin_col],
            mode = 'markers',
            marker = dict(
                size = 2,
                color = 'rgb(0, 0, 0)',
                line = dict(width = 3, color = 'rgba(68, 68, 68, 0)')
            )
        ))

        # Add traces for each shipment route
        shipment_id_col = ColumnMapper.get_column_if_exists(df, 'shipmentid')
        for index, row in df.iterrows():
            fig_map.add_trace(go.Scattergeo(
                locationmode = 'USA-states',
                lon = [row[origin_lon_col], row[dest_lon_col]],
                lat = [row[origin_lat_col], row[dest_lat_col]],
                mode = 'lines',
                line = dict(width = 1, color = 'red'),
                name=f"Shipment {row[shipment_id_col] if shipment_id_col else index}",
                opacity = 0.5
            ))
        
        # Configure map layout
        fig_map.update_layout(
            showlegend = False,
            title_text = 'Shipment Routes',
            geo = dict(
                scope = 'world',
                projection_type = 'mercator',
                showland = True,
                landcolor = 'rgb(243, 243, 243)',
                countrycolor = 'rgb(204, 204, 204)',
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        required_display_names = [
            ColumnMapper.get_display_name('origin'),
            ColumnMapper.get_display_name('destination'),
            'Origin Lat', 'Origin Lon', 'Dest Lat', 'Dest Lon'
        ]
        st.info(
            f"ℹ️ The geographic map visualization requires columns for geographic data. "
            f"Expected columns: `{', '.join(required_display_names)}`."
        )