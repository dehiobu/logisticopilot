# route_optimization_tab.py
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 3959  # Earth's radius in miles
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c
    
    return distance

def create_route_map(df, origin_lat_col, origin_lon_col, dest_lat_col, dest_lon_col, origin_col=None, dest_col=None, cost_col=None):
    """Create an interactive map showing all routes"""
    # Calculate center point
    center_lat = (df[origin_lat_col].mean() + df[dest_lat_col].mean()) / 2
    center_lon = (df[origin_lon_col].mean() + df[dest_lon_col].mean()) / 2
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
    
    # Color mapping for different carriers
    carrier_colors = {
        'FedEx': 'purple',
        'UPS': 'brown', 
        'DHL': 'orange',
        'USPS': 'blue',
        'DPD': 'green'
    }
    
    # Add routes
    for idx, row in df.iterrows():
        # Get carrier name (check multiple possible column names)
        carrier = 'Unknown'
        for col in ['Carrier', 'carrier', 'CARRIER']:
            if col in row and pd.notna(row[col]):
                carrier = str(row[col])
                break
        
        # Get origin and destination names
        origin_name = row[origin_col] if origin_col and origin_col in row else 'Unknown'
        dest_name = row[dest_col] if dest_col and dest_col in row else 'Unknown'
        
        # Get shipment ID
        shipment_id = 'Unknown'
        for col in ['Shipment ID', 'shipment_id', 'shipment id', 'id']:
            if col in row and pd.notna(row[col]):
                shipment_id = str(row[col])
                break
        
        # Get cost
        cost_value = 0
        if cost_col and cost_col in row and pd.notna(row[cost_col]):
            cost_value = float(row[cost_col])
        
        color = carrier_colors.get(carrier, 'gray')
        
        # Origin marker
        folium.Marker(
            [row[origin_lat_col], row[origin_lon_col]],
            popup=f"<b>Origin:</b> {origin_name}<br><b>Carrier:</b> {carrier}<br><b>ID:</b> {shipment_id}",
            icon=folium.Icon(color='green', icon='play')
        ).add_to(m)
        
        # Destination marker
        folium.Marker(
            [row[dest_lat_col], row[dest_lon_col]],
            popup=f"<b>Destination:</b> {dest_name}<br><b>Carrier:</b> {carrier}<br><b>Cost:</b> ${cost_value:.2f}",
            icon=folium.Icon(color='red', icon='stop')
        ).add_to(m)
        
        # Calculate distance
        distance = calculate_distance(
            row[origin_lat_col], row[origin_lon_col],
            row[dest_lat_col], row[dest_lon_col]
        )
        
        # Route line
        folium.PolyLine(
            [[row[origin_lat_col], row[origin_lon_col]], 
             [row[dest_lat_col], row[dest_lon_col]]],
            color=color,
            weight=3,
            opacity=0.7,
            popup=f"<b>Route:</b> {origin_name} → {dest_name}<br><b>Distance:</b> {distance:.0f} miles<br><b>Carrier:</b> {carrier}<br><b>Cost:</b> ${cost_value:.2f}"
        ).add_to(m)
    
    return m

def show_route_optimization_tab(df: pd.DataFrame):
    """
    Displays content for the Route Optimization tab with full functionality.

    Args:
        df (pd.DataFrame): The manifest data with coordinates.
    """
    st.header("🚚 Route Optimization")
    st.write("Analyze and optimize your logistics routes for better efficiency and cost savings.")

    if df is None or df.empty:
        st.info("📁 Please upload a logistics manifest file to analyze routes.")
        return

    # Check for coordinate columns (flexible detection)
    origin_lat_col = None
    origin_lon_col = None
    dest_lat_col = None
    dest_lon_col = None
    
    # Find coordinate columns (case-insensitive)
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
    
    has_coords = all([origin_lat_col, origin_lon_col, dest_lat_col, dest_lon_col])
    
    if not has_coords:
        st.warning("⚠️ No coordinate data found. Please generate coordinates in the Data Mapping tab first.")
        st.info("Looking for columns containing: origin+lat, origin+lon, dest+lat, dest+lon")
        
        # Show what columns are available
        st.subheader("Available Columns:")
        for i, col in enumerate(df.columns, 1):
            st.write(f"{i}. {col}")
        return
    
    # Success! We have coordinate data
    st.success(f"✅ Found coordinate data for {len(df)} shipments")
    
    # Calculate route metrics using detected column names
    df_with_distances = df.copy()
    df_with_distances['Distance_Miles'] = df_with_distances.apply(
        lambda row: calculate_distance(
            row[origin_lat_col], row[origin_lon_col],
            row[dest_lat_col], row[dest_lon_col]
        ), axis=1
    )
    
    # Add cost per mile if cost column exists (check multiple possible names)
    cost_col = None
    for col in df.columns:
        if col.lower() == 'cost':
            cost_col = col
            break
    
    # Find origin and destination columns (flexible detection)
    origin_col = None
    dest_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'origin' in col_lower and not any(x in col_lower for x in ['lat', 'lon']):
            origin_col = col
        elif ('destination' in col_lower or 'dest' in col_lower) and not any(x in col_lower for x in ['lat', 'lon']):
            dest_col = col
    
    st.write(f"Origin column detected: {origin_col}")
    st.write(f"Destination column detected: {dest_col}")
    if origin_col:
        st.write(f"Sample origins: {df[origin_col].head().tolist()}")
    if dest_col:
        st.write(f"Sample destinations: {df[dest_col].head().tolist()}")
    
    if cost_col:
        df_with_distances['Cost_Per_Mile'] = df_with_distances[cost_col] / df_with_distances['Distance_Miles']
        df_with_distances['Cost_Per_Mile'] = df_with_distances['Cost_Per_Mile'].round(4)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_distance = df_with_distances['Distance_Miles'].sum()
        st.metric("Total Distance", f"{total_distance:,.0f} miles")
    
    with col2:
        avg_distance = df_with_distances['Distance_Miles'].mean()
        st.metric("Average Distance", f"{avg_distance:,.0f} miles")
    
    with col3:
        if cost_col:
            total_cost = df[cost_col].sum()
            st.metric("Total Cost", f"${total_cost:,.2f}")
        else:
            st.metric("Total Cost", "N/A")
    
    with col4:
        if cost_col and total_distance > 0:
            avg_cost_per_mile = df[cost_col].sum() / total_distance
            st.metric("Avg Cost/Mile", f"${avg_cost_per_mile:.3f}")
        else:
            st.metric("Avg Cost/Mile", "N/A")
    
    # Interactive Map
    st.markdown("---")
    st.subheader("📍 Route Visualization")
    
    # Create and display map
    route_map = create_route_map(df_with_distances, origin_lat_col, origin_lon_col, dest_lat_col, dest_lon_col, origin_col, dest_col, cost_col)
    st_folium(route_map, width=700, height=400)
    
    # Route Analysis
    st.markdown("---")
    st.subheader("📊 Route Analysis")
    
    # Show detailed route data
    display_cols = []
    
    # Add shipment ID column
    for col in ['Shipment ID', 'shipment_id', 'shipment id', 'id']:
        if col in df_with_distances.columns:
            display_cols.append(col)
            break
    
    # Add origin and destination columns
    if origin_col:
        display_cols.append(origin_col)
    if dest_col:
        display_cols.append(dest_col)
    
    # Add carrier column
    for col in ['Carrier', 'carrier', 'CARRIER']:
        if col in df_with_distances.columns:
            display_cols.append(col)
            break
    
    # Add distance and cost columns
    display_cols.append('Distance_Miles')
    if cost_col:
        display_cols.extend([cost_col, 'Cost_Per_Mile'])
    
    # Add status column
    for col in ['Status', 'status', 'STATUS']:
        if col in df_with_distances.columns:
            display_cols.append(col)
            break
    
    # Filter columns that actually exist
    available_display_cols = [col for col in display_cols if col in df_with_distances.columns]
    
    st.dataframe(
        df_with_distances[available_display_cols].round(2),
        use_container_width=True
    )
    
    # Optimization Insights
    st.markdown("---")
    st.subheader("💡 Optimization Insights")
    
    # Find longest and shortest routes
    longest_route = df_with_distances.loc[df_with_distances['Distance_Miles'].idxmax()]
    shortest_route = df_with_distances.loc[df_with_distances['Distance_Miles'].idxmin()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        origin_name = longest_route[origin_col] if origin_col else 'Unknown'
        dest_name = longest_route[dest_col] if dest_col else 'Unknown'
        st.info(f"**Longest Route:** {origin_name} → {dest_name}")
        st.write(f"Distance: {longest_route['Distance_Miles']:.0f} miles")
        if cost_col:
            st.write(f"Cost: ${longest_route[cost_col]:.2f}")
            st.write(f"Cost per mile: ${longest_route.get('Cost_Per_Mile', 0):.3f}")
    
    with col2:
        origin_name = shortest_route[origin_col] if origin_col else 'Unknown'
        dest_name = shortest_route[dest_col] if dest_col else 'Unknown'
        st.info(f"**Shortest Route:** {origin_name} → {dest_name}")
        st.write(f"Distance: {shortest_route['Distance_Miles']:.0f} miles")
        if cost_col:
            st.write(f"Cost: ${shortest_route[cost_col]:.2f}")
            st.write(f"Cost per mile: ${shortest_route.get('Cost_Per_Mile', 0):.3f}")
    
    # Cost efficiency analysis
    if cost_col:
        st.markdown("---")
        st.subheader("💰 Cost Efficiency Analysis")
        
        # Most and least cost-efficient routes
        most_efficient = df_with_distances.loc[df_with_distances['Cost_Per_Mile'].idxmin()]
        least_efficient = df_with_distances.loc[df_with_distances['Cost_Per_Mile'].idxmax()]
        
        col1, col2 = st.columns(2)
        
        with col1:
            origin_name = most_efficient[origin_col] if origin_col else 'Unknown'
            dest_name = most_efficient[dest_col] if dest_col else 'Unknown'
            carrier_name = 'Unknown'
            for col in ['Carrier', 'carrier', 'CARRIER']:
                if col in most_efficient and pd.notna(most_efficient[col]):
                    carrier_name = str(most_efficient[col])
                    break
            
            st.success(f"**Most Cost-Efficient:** {origin_name} → {dest_name}")
            st.write(f"Cost per mile: ${most_efficient['Cost_Per_Mile']:.3f}")
            st.write(f"Total cost: ${most_efficient[cost_col]:.2f}")
            st.write(f"Carrier: {carrier_name}")
        
        with col2:
            origin_name = least_efficient[origin_col] if origin_col else 'Unknown'
            dest_name = least_efficient[dest_col] if dest_col else 'Unknown'
            carrier_name = 'Unknown'
            for col in ['Carrier', 'carrier', 'CARRIER']:
                if col in least_efficient and pd.notna(least_efficient[col]):
                    carrier_name = str(least_efficient[col])
                    break
            
            st.error(f"**Least Cost-Efficient:** {origin_name} → {dest_name}")
            st.write(f"Cost per mile: ${least_efficient['Cost_Per_Mile']:.3f}")
            st.write(f"Total cost: ${least_efficient[cost_col]:.2f}")
            st.write(f"Carrier: {carrier_name}")
    
    # Carrier analysis
    if 'Carrier' in df.columns:
        st.markdown("---")
        st.subheader("🚛 Carrier Performance")
        
        carrier_stats = df_with_distances.groupby('Carrier').agg({
            'Distance_Miles': ['count', 'sum', 'mean'],
            cost_col: ['sum', 'mean'] if cost_col else [],
            'Cost_Per_Mile': ['mean'] if cost_col else []
        }).round(3)
        
        # Flatten column names
        carrier_stats.columns = ['_'.join(col).strip() for col in carrier_stats.columns]
        carrier_stats = carrier_stats.reset_index()
        
        st.dataframe(carrier_stats, use_container_width=True)
    
    # Download enhanced data
    st.markdown("---")
    st.subheader("📥 Download Enhanced Data")
    
    csv_with_analysis = df_with_distances.to_csv(index=False)
    st.download_button(
        "📊 Download Route Analysis Data",
        data=csv_with_analysis,
        file_name=f"route_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        help="Download your data with distance calculations and route analysis"
    )