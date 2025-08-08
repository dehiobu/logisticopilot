# ==============================================================================
# 📦 LogiBot AI Copilot – Main App
# ==============================================================================
import streamlit as st
import pandas as pd
from langchain.docstore.document import Document
import os
import io

# Add these imports to the top of your app.py file
import requests # Added for geocoding
import time # Added for geocoding rate limiting
from urllib.parse import quote # Added for geocoding URL encoding

from utils.geocoding_utils import (
    add_geographic_coordinates,
    generate_sample_coordinates_file,
    validate_geographic_data
)


# Check if running in development mode (which causes auto-reloads)
if "dev_mode_detected" not in st.session_state:
    st.session_state.dev_mode_detected = os.environ.get('STREAMLIT_SERVER_RUN_ON_SAVE', 'false').lower() == 'true'


# --- Custom modules from the 'utils' subdirectory ---
from config import OPENAI_API_KEY
from utils.llm_utils import summarize_manifest, answer_question, get_retriever, get_data_overview # Added get_data_overview
from utils.carrier_utils import load_approved_carriers, save_approved_carriers
from utils.excel_utils import export_manifest_to_excel
from utils.column_utils import (
    normalize_column_names,
    detect_column_mapping,
    validate_required_columns,
    display_column_analysis,
    create_column_mapping_interface,
    apply_column_mapping,
    clean_column_data
)
from tabs.dashboard_tab import show_dashboard_tab
from tabs.ai_documentation_tab import show_ai_documentation_tab
from tabs.route_optimization_tab import show_route_optimization_tab
from tabs.shipment_alert_tab import shipment_alert_tab
from tabs.llm_query_tab import show_llm_query_tab
from tabs.timeline_tab import show_timeline_tab



# ------------------------------------------------------------------------------
# 1. Page Configuration and Main UI
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="LogiBot AI Copilot",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 LogiBot AI Copilot")
st.subheader("Your AI assistant for logistics manifest analysis.")


# ------------------------------------------------------------------------------
# 2. State Management
# ------------------------------------------------------------------------------
# Initialize session state variables to ensure they persist across reruns.
if "approved_carriers" not in st.session_state:
    st.session_state.approved_carriers = load_approved_carriers()
if "ai_summary" not in st.session_state:
    st.session_state.ai_summary = "No AI summary has been generated yet."
if "df" not in st.session_state:
    st.session_state.df = None
if "df_original" not in st.session_state:
    st.session_state.df_original = None
if "documents" not in st.session_state:
    st.session_state.documents = []
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = {}
if "data_processed" not in st.session_state:
    st.session_state.data_processed = False
if "geocoding_completed" not in st.session_state:
    st.session_state.geocoding_completed = False
if "geocoding_timestamp" not in st.session_state:
    st.session_state.geocoding_timestamp = None
if "debug_info" not in st.session_state:
    st.session_state.debug_info = []



# ------------------------------------------------------------------------------
# 3. File Uploader and Data Processing
# ------------------------------------------------------------------------------
st.sidebar.header("📁 Upload Manifest")
uploaded_file = st.sidebar.file_uploader(
    "Choose a CSV or XLSX file",
    type=["csv", "xlsx"],
    help="Upload your logistics manifest file for analysis"
)

if uploaded_file is not None:
    try:
        # Read the file
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        # Store original data
        st.session_state.df_original = df_raw.copy()

        # Normalize column names to lowercase to avoid case-sensitivity issues
        # Deduplicate columns first (e.g. from repeated enhancements)
        df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]

        # Normalize column names to lowercase to avoid case-sensitivity issues
        df_normalized = normalize_column_names(df_raw)

        # Store processed data
        st.session_state.df = df_normalized
        st.session_state.data_processed = True

        # Auto-detect column mapping
        st.session_state.column_mapping = detect_column_mapping(df_normalized)

        st.success("✅ File uploaded and processed successfully!")

        # Show basic file info
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 File Info")
        st.sidebar.write(f"**Rows:** {len(df_normalized)}")
        st.sidebar.write(f"**Columns:** {len(df_normalized.columns)}")

        # Show validation status
        is_valid, missing_cols = validate_required_columns(df_normalized)
        if is_valid:
            st.sidebar.success("✅ Required columns detected")
        else:
            st.sidebar.warning(f"⚠️ Missing: {', '.join(missing_cols)}")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
        st.session_state.df = None
        st.session_state.df_original = None
        st.session_state.data_processed = False
elif st.sidebar.button("Clear Data", help="Remove uploaded data and reset"):
    # Clear all data-related session state
    st.session_state.df = None
    st.session_state.df_original = None
    st.session_state.data_processed = False
    st.session_state.column_mapping = {}
    st.session_state.ai_summary = "No AI summary has been generated yet."
    st.session_state.documents = []
    if "retriever" in st.session_state:
        del st.session_state.retriever
    st.rerun()

df = st.session_state.df


# ------------------------------------------------------------------------------
# 4. Sidebar for Approved Carriers
# ------------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚚 Approved Carriers")

# Show carrier count
carrier_count = len(st.session_state.approved_carriers)
st.sidebar.write(f"**Total carriers:** {carrier_count}")

# Expandable carrier management
with st.sidebar.expander("Manage Carriers", expanded=False):
    approved_carriers_text = st.text_area(
        "Edit approved carriers (one per line)",
        value="\n".join(st.session_state.approved_carriers),
        height=150,
        key="carrier_text_area"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Carriers", key="save_carriers"):
            new_carriers = [c.strip() for c in approved_carriers_text.splitlines() if c.strip()]
            st.session_state.approved_carriers = sorted(list(set(new_carriers)))
            save_approved_carriers(st.session_state.approved_carriers)
            st.success("✅ Saved!")

    with col2:
        if st.button("Reset to Default", key="reset_carriers"):
            # You can define default carriers here
            default_carriers = ["FedEx", "UPS", "DHL", "USPS"]
            st.session_state.approved_carriers = default_carriers
            save_approved_carriers(st.session_state.approved_carriers)
            st.success("✅ Reset!")
            st.rerun()


# ------------------------------------------------------------------------------
# 5. API Key Validation
# ------------------------------------------------------------------------------
if not OPENAI_API_KEY:
    st.error("❌ OpenAI API key not found. Please check your configuration.")
    st.info("💡 Make sure to set your OPENAI_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

# ------------------------------------------------------------------------------
# 5.5. Sample Data Section for Testing
# ------------------------------------------------------------------------------

# --- Sample Data Section ---
st.markdown("---")
st.markdown("### 📂 **Sample Data for Testing**")
st.info("💡 **New to LogiBot?** Download these sample files to test all features instantly!")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🚚 Basic Manifest**")
    st.markdown("*Tests: AI Summary, Q&A, Dashboard*")
    st.caption("*7 columns • Standard logistics format*")
    
    # Using your 7-column structure from sample_logistics_manifest2.csv
    basic_data = """Shipment ID,Carrier,Status,Cost,Tracking Ref,Origin,Destination
SHP001,DHL,Delivered,25.50,DHL123456,London,Manchester
SHP002,FedEx,In Transit,45.20,FDX789012,Birmingham,Edinburgh
SHP003,UPS,Delayed,32.75,UPS345678,Bristol,Glasgow
SHP004,DPD,Delivered,18.90,DPD901234,Cardiff,Newcastle
SHP005,Royal Mail,In Transit,12.25,RM567890,Liverpool,Leeds
SHP006,Amazon Logistics,Delivered,28.75,AMZN345678,Nottingham,Sheffield
SHP007,Hermes,Processing,35.60,HMS789012,Southampton,Portsmouth
SHP008,TNT,Delayed,41.90,TNT234567,Oxford,Cambridge
SHP009,UPS,Delivered,29.45,UPS987321,York,Hull
SHP010,DPD,In Transit,33.80,DPD456789,Preston,Blackpool
SHP011,FedEx,Delivered,52.30,FDX654987,Bath,Exeter
SHP012,DHL,Processing,38.75,DHL789456,Coventry,Wolverhampton
SHP013,Royal Mail,Delivered,15.60,RM321654,Norwich,Ipswich"""
    
    st.download_button(
        "📥 Download Basic Sample",
        data=basic_data,
        file_name="basic_logistics_manifest.csv",
        mime="text/csv",
        help="13 shipments • Tests AI Summary & Q&A",
        key="basic_download"
    )

with col2:
    st.markdown("**🌍 Enhanced Manifest**")
    st.markdown("*Tests: Route Optimization, Maps*")
    st.caption("*15 columns • With coordinates & dates*")
    
    # Using your 15-column structure from manifest_with_coordinates
    enhanced_data = """shipment_id,carrier,status,cost,tracking_ref,origin,destination,priority,departure_date,expected_arrival,delivery_date,Origin Lat,Origin Lon,Dest Lat,Dest Lon
SHP001,DHL,Delivered,25.50,DHL123456,London,Manchester,High,2024-08-01,2024-08-02,2024-08-02,51.5074,-0.1278,53.4808,-2.2426
SHP002,FedEx,In Transit,45.20,FDX789012,Birmingham,Edinburgh,Medium,2024-08-03,2024-08-04,,52.4862,-1.8904,55.9533,-3.1883
SHP003,UPS,Delayed,32.75,UPS345678,Bristol,Glasgow,High,2024-08-02,2024-08-03,,51.4545,-2.5879,55.8642,-4.2518
SHP004,DPD,Delivered,18.90,DPD901234,Cardiff,Newcastle,Low,2024-08-01,2024-08-02,2024-08-02,51.4816,-3.1791,54.9783,-1.6178
SHP005,Royal Mail,In Transit,12.25,RM567890,Liverpool,Leeds,Medium,2024-08-04,2024-08-05,,53.4084,-2.9916,53.8008,-1.5491
SHP006,Amazon Logistics,Delivered,28.75,AMZN345678,Nottingham,Sheffield,High,2024-08-01,2024-08-03,2024-08-03,52.9548,-1.1581,53.3811,-1.4701
SHP007,Hermes,Processing,35.60,HMS789012,Southampton,Portsmouth,Low,2024-08-05,2024-08-06,,50.9097,-1.4044,50.8050,-1.0872
SHP008,TNT,Delayed,41.90,TNT234567,Oxford,Cambridge,Medium,2024-08-02,2024-08-04,,51.7520,-1.2577,52.2053,0.1218
SHP009,UPS,Delivered,29.45,UPS987321,York,Hull,Low,2024-08-03,2024-08-04,2024-08-04,53.9600,-1.0873,53.7676,-0.3274
SHP010,DPD,In Transit,33.80,DPD456789,Preston,Blackpool,Medium,2024-08-04,2024-08-05,,53.7632,-2.7031,53.8175,-3.0357"""
    
    st.download_button(
        "📥 Download Enhanced Sample",
        data=enhanced_data,
        file_name="enhanced_logistics_manifest.csv",
        mime="text/csv",
        help="10 shipments • Tests Route Optimization",
        key="enhanced_download"
    )

with col3:
    st.markdown("**⚠️ Problem Manifest**")
    st.markdown("*Tests: Compliance Alerts, Validation*")
    st.caption("*7 columns • Contains compliance issues*")
    
    # Problem data using your basic structure but with compliance issues
    problem_data = """Shipment ID,Carrier,Status,Cost,Tracking Ref,Origin,Destination
SHP020,UnauthorizedCarrier,Delayed,125.50,,London,Paris
SHP021,SketchyLogistics,Failed,85.20,FAKE001,Manchester,Dublin
SHP022,FakeTransport,In Transit,99.99,INVALID123,Liverpool,Cork
SHP023,,Processing,0.00,,Birmingham,Belfast
SHP024,UnknownCarrier,Cancelled,75.00,NO_TRACK,Bristol,Cardiff
SHP025,DHL,Delivered,22.75,DHL987654,Leeds,York
SHP026,BadCarrier,Delayed,156.90,,Newcastle,Glasgow
SHP027,UPS,In Transit,45.60,UPS123789,Southampton,Brighton
SHP028,,Failed,0.00,MISSING_REF,Plymouth,Exeter
SHP029,IllegalTransport,Processing,89.45,,Swansea,Newport"""
    
    st.download_button(
        "📥 Download Problem Sample",
        data=problem_data,
        file_name="problem_logistics_manifest.csv",
        mime="text/csv",
        help="10 shipments • Tests Compliance Checking",
        key="problem_download"
    )

# Quick instructions
st.markdown("### 🚀 **Quick Test Instructions**")
with st.expander("👁️ Click to see testing guide", expanded=False):
    st.markdown("""
    **Step 1:** Click any download button above  
    **Step 2:** Upload the downloaded CSV file using the sidebar file uploader  
    **Step 3:** Explore these features:
    
    **📊 Dashboard Tab:**
    - View automatic KPI calculations
    - See carrier distribution charts
    - Cost analysis and trends
    
    **🤖 AI Insights Tab:**  
    - Ask: *"How many shipments are delayed?"*
    - Ask: *"Which carrier has the most shipments?"*
    - Ask: *"What's the total cost?"*
    
    **📋 Data Mapping Tab:**
    - Generate coordinates for basic manifest
    - Download enhanced data with lat/lon
    
    **✅ Carrier Check Tab:**
    - See approved vs unapproved carriers
    - Test with problem manifest for alerts
    
    **🚚 Route Optimization Tab:**
    - Upload enhanced manifest with coordinates
    - View interactive maps and routes
    
    **📥 Reports Tab:**
    - Export to Excel with AI summaries
    - Generate PDF reports
    
    **💡 Pro Tips:**
    - Try **Basic Sample** first for core AI features
    - Use **Enhanced Sample** for mapping features  
    - Try **Problem Sample** to see compliance alerts in action
    """)

st.markdown("---")

# ------------------------------------------------------------------------------
# 6. Tab Navigation and Content Display
# ------------------------------------------------------------------------------
# Create tabs for different functionalities
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 Dashboard",
    "🤖 AI Insights",
    "📋 Data Mapping",
    "✅ Carrier Check",
    "🚚 Route Optimization",
    "📥 Reports",
    "🚨 Shipment Alerts",
    "📚 AI Documentation",
    "⏳ Timeline"
])

# Use the tabs for different features based on the uploaded data
with tab1:
    show_dashboard_tab(df)

with tab2:
    show_llm_query_tab(df)


with tab3:
    st.write("🔍 **Session State Debug:**")
    current_df = st.session_state.get('df')

    if current_df is not None:
        st.write(f"Session DF columns: {len(current_df.columns)}")
        coord_cols_found = [col for col in current_df.columns if any(x in col for x in ['Lat', 'Lon'])]
        st.write(f"Coordinate columns in session: {coord_cols_found}")

        # ✅ Debug flags
        if st.session_state.get('geocoding_completed', False):
            st.success(f"✅ Geocoding completed: {st.session_state.get('geocoding_timestamp', 'Unknown time')}")
        else:
            st.warning("⚠️ No geocoding completion flag found")

        # ✅ Debug history
        if st.session_state.get('debug_info'):
            with st.expander("🔍 Debug History"):
                for info in st.session_state.debug_info:
                    st.write(f"• {info}")
    else:
        st.write("No DF in session state")

    # ✅ Dev mode warning
    if st.session_state.dev_mode_detected:
        st.warning("⚠️ Development mode detected - auto-reloads may cause data loss")

    # Get the current df from session state for this tab too
    current_df = st.session_state.get('df')
    
    st.header("📋 Data Column Mapping")
    st.write("Analyze and map your data columns to standard logistics fields.")

    if current_df is not None and not current_df.empty:
        # Display column analysis
        display_column_analysis(current_df)
        
        st.markdown("---")
        
        # Manual column mapping interface
        if st.checkbox("🔧 Manual Column Mapping", help="Manually adjust column mappings"):
            user_mapping = create_column_mapping_interface(current_df)
            
            if st.button("Apply Column Mapping"):
                if user_mapping:
                    # Apply the mapping and clean the data
                    df_mapped = apply_column_mapping(current_df, user_mapping)
                    df_cleaned = clean_column_data(df_mapped, user_mapping)
                    
                    # Update session state
                    st.session_state.df = df_cleaned
                    st.session_state.column_mapping = user_mapping
                    
                    st.success("✅ Column mapping applied successfully!")
                    st.rerun()
                else:
                    st.warning("⚠️ No column mappings selected.")
        
        # Show current mapping
        if st.session_state.column_mapping:
            st.subheader("🗺️ Current Column Mapping")
            mapping_df = pd.DataFrame([
                {"Standard Field": k.replace('_', ' ').title(), "Your Column": v}
                for k, v in st.session_state.column_mapping.items()
                if v is not None
            ])
            st.dataframe(mapping_df, use_container_width=True)

        # --- Geographic Data Generation Section ---
        st.markdown("---")
        st.subheader("🌍 Geographic Data Generation")
        st.write("Generate latitude and longitude coordinates for map visualizations.")
        
        # Check if we have origin and destination columns
        has_origin = any('origin' in col.lower() for col in current_df.columns)
        has_destination = any('destination' in col.lower() or 'dest' in col.lower() for col in current_df.columns)
        
        if has_origin and has_destination:
            # Check if coordinates already exist (check session state first, then current_df)
            session_df = st.session_state.get('df')
            if session_df is not None:
                has_coords = all(col in session_df.columns for col in ['Origin Lat', 'Origin Lon', 'Dest Lat', 'Dest Lon'])
                # Use session_df for the rest of this section when coordinates exist
                df_to_use = session_df
            else:
                has_coords = all(col in current_df.columns for col in ['Origin Lat', 'Origin Lon', 'Dest Lat', 'Dest Lon'])
                df_to_use = current_df
            
            if has_coords:
                # Show existing coordinate data
                coord_cols = ['origin', 'destination', 'Origin Lat', 'Origin Lon', 'Dest Lat', 'Dest Lon']
                available_coord_cols = [col for col in coord_cols if col in df_to_use.columns]
                
                st.success("✅ Geographic coordinates already exist in your data!")
                if available_coord_cols:
                    st.dataframe(df_to_use[available_coord_cols].head(), use_container_width=True)
                
                # Validate coordinate quality
                if all(col in df_to_use.columns for col in ['Origin Lat', 'Origin Lon', 'Dest Lat', 'Dest Lon']):
                    valid_origins = df_to_use[['Origin Lat', 'Origin Lon']].notna().all(axis=1).sum()
                    valid_destinations = df_to_use[['Dest Lat', 'Dest Lon']].notna().all(axis=1).sum()
                    total_rows = len(df_to_use)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Shipments", total_rows)
                    with col2:
                        st.metric("Origins with Coordinates", f"{valid_origins}/{total_rows}")
                    with col3:
                        st.metric("Destinations with Coordinates", f"{valid_destinations}/{total_rows}")
                
                # Option to regenerate coordinates
                if st.button("🔄 Regenerate Coordinates", help="Regenerate coordinates for missing or invalid data"):
                    with st.spinner("Regenerating geographic coordinates..."):
                        df_with_coords = add_geographic_coordinates(df_to_use)
                        st.session_state.df = df_with_coords
                        st.success("✅ Coordinates regenerated!")

            # Check if we have enhanced data ready for download
            if st.session_state.get('coordinates_ready_for_download', False):
                st.success("✅ Enhanced data with coordinates is ready!")
                
                # Show download button
                st.download_button(
                    "📥 Download Data with Coordinates",
                    data=st.session_state.get('enhanced_csv_data', ''),
                    file_name=st.session_state.get('download_filename', 'manifest_with_coordinates.csv'),
                    mime="text/csv",
                    help="Download your data with the new geographic coordinates",
                    key="persistent_download_button"
                )
                
                st.info("💡 **Next Steps:** Download the file above, then re-upload it to use route optimization features!")
                
                # Option to clear the download data
                if st.button("🗑️ Clear Download Data", help="Remove the enhanced data to generate new coordinates"):
                    st.session_state.coordinates_ready_for_download = False
                    if 'enhanced_csv_data' in st.session_state:
                        del st.session_state.enhanced_csv_data
                    if 'download_filename' in st.session_state:
                        del st.session_state.download_filename
                    st.rerun()
                
                st.markdown("---")
                
            if not has_coords:
                # Generate coordinates for the first time
                st.info("📍 Your data contains Origin and Destination columns but no coordinate data.")
                
                # Find origin and destination columns
                origin_col = None
                dest_col = None
                
                for col in current_df.columns:
                    if 'origin' in col.lower():
                        origin_col = col
                        break
                
                for col in current_df.columns:
                    if 'destination' in col.lower() or 'dest' in col.lower():
                        dest_col = col
                        break
                
                if origin_col and dest_col:
                    # Show preview of cities that will be geocoded
                    unique_origins = current_df[origin_col].dropna().unique()
                    unique_destinations = current_df[dest_col].dropna().unique()
                    all_unique_cities = set(list(unique_origins) + list(unique_destinations))
                    
                    st.write(f"**Cities to geocode:** {len(all_unique_cities)} unique locations")
                    
                    # Show sample cities
                    with st.expander("📋 Preview cities to be geocoded"):
                        cities_preview = list(all_unique_cities)[:10]  # Show first 10
                        for city in cities_preview:
                            st.write(f"• {city}")
                        if len(all_unique_cities) > 10:
                            st.write(f"... and {len(all_unique_cities) - 10} more")
                    
                    # Warning about API usage
                    st.warning(
                        "⚠️ This will use the free OpenStreetMap Nominatim geocoding service. "
                        "Large datasets may take several minutes to process."
                    )
                    
                    if st.button("🌍 Generate Geographic Coordinates", type="primary"):
                        try:
                            with st.spinner("Geocoding cities... This may take a few minutes for large datasets."):
                                import requests
                                import time
                                
                                def geocode_location(location_name):
                                    """Geocode a single location using Nominatim API"""
                                    if pd.isna(location_name) or not location_name.strip():
                                        return None, None
                                    
                                    # Clean location name
                                    location = str(location_name).strip()
                                    
                                    # Nominatim API endpoint
                                    url = f"https://nominatim.openstreetmap.org/search"
                                    params = {
                                        'q': location,
                                        'format': 'json',
                                        'limit': 1,
                                        'addressdetails': 1
                                    }
                                    
                                    headers = {
                                        'User-Agent': 'LogiBotAI/1.0'
                                    }
                                    
                                    try:
                                        response = requests.get(url, params=params, headers=headers, timeout=10)
                                        
                                        if response.status_code == 200:
                                            data = response.json()
                                            if data:
                                                return float(data[0]['lat']), float(data[0]['lon'])
                                        
                                        return None, None
                                        
                                    except Exception:
                                        return None, None
                                
                                # Create enhanced dataframe
                                df_with_coords = current_df.copy()
                                
                                st.write(f"🔍 **Geocoding Debug:**")
                                st.write(f"Origin column found: {origin_col}")
                                st.write(f"Destination column found: {dest_col}")
                                
                                # Get unique locations to minimize API calls
                                locations_to_geocode = set()
                                locations_to_geocode.update(current_df[origin_col].dropna().unique())
                                locations_to_geocode.update(current_df[dest_col].dropna().unique())
                                
                                st.write(f"Cities to geocode: {len(locations_to_geocode)}")
                                
                                # Create progress tracking
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                # Geocode locations
                                location_coords = {}
                                for i, location in enumerate(locations_to_geocode):
                                    progress = (i + 1) / len(locations_to_geocode)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Geocoding: {location}")
                                    
                                    lat, lon = geocode_location(location)
                                    location_coords[location] = (lat, lon)
                                    
                                    # Rate limiting - be respectful to the API
                                    time.sleep(1)
                                
                                # Add coordinates to dataframe
                                df_with_coords['Origin Lat'] = df_with_coords[origin_col].map(lambda x: location_coords.get(x, (None, None))[0])
                                df_with_coords['Origin Lon'] = df_with_coords[origin_col].map(lambda x: location_coords.get(x, (None, None))[1])
                                df_with_coords['Dest Lat'] = df_with_coords[dest_col].map(lambda x: location_coords.get(x, (None, None))[0])
                                df_with_coords['Dest Lon'] = df_with_coords[dest_col].map(lambda x: location_coords.get(x, (None, None))[1])
                                
                                # Count successful geocodes
                                origin_success = df_with_coords['Origin Lat'].notna().sum()
                                dest_success = df_with_coords['Dest Lat'].notna().sum()
                                
                                # Clear progress indicators
                                progress_bar.empty()
                                status_text.empty()
                                
                                # Show results BEFORE updating session state
                                st.success("✅ Geocoding complete!")
                                st.info(f"📍 Successfully geocoded {origin_success}/{len(current_df)} origins and {dest_success}/{len(current_df)} destinations")
                                
                                # Debug: Show new columns
                                st.write(f"🔍 **Enhanced Data Debug:**")
                                st.write(f"Original columns: {len(current_df.columns)}")
                                st.write(f"Enhanced columns: {len(df_with_coords.columns)}")
                                st.write(f"New columns added: {list(df_with_coords.columns)[-4:]}")
                                
                                # CRITICAL: Update session state with enhanced data
                                st.session_state.df = df_with_coords
                                
                                # Store the enhanced data in session state for download
                                st.session_state.enhanced_csv_data = df_with_coords.to_csv(index=False)
                                st.session_state.download_filename = f"manifest_with_coordinates_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
                                st.session_state.coordinates_ready_for_download = True
                                
                                # Verify session state was updated
                                if 'df' in st.session_state and st.session_state.df is not None:
                                    session_cols = len(st.session_state.df.columns)
                                    st.success(f"✅ Session state updated! Now has {session_cols} columns")
                                    
                                    # Show coordinate columns specifically
                                    coord_cols_in_session = [col for col in st.session_state.df.columns if any(x in col for x in ['Lat', 'Lon'])]
                                    st.info(f"Coordinate columns in session: {coord_cols_in_session}")
                                else:
                                    st.error("❌ Failed to update session state")
                                
                                # Show next steps
                                st.success("🎯 **Next Steps:**")
                                st.write("✅ Coordinates have been added to your data")
                                st.write("🗺️ Go to **Route Optimization** tab to see route maps and analysis")
                                st.write("⏳ Go to **Timeline** tab for shipment timeline visualization")
                                st.write("📊 All other tabs now have access to the enhanced data")
                                st.info("💡 **Important:** The download button will appear above after the page updates. Download the enhanced data file and re-upload it for reliable route optimization!")
                                
                        except ImportError as e:
                            st.error(f"❌ Missing required library: {e}")
                            st.info("Please install: pip install requests")
                        except Exception as e:
                            st.error(f"❌ Geocoding failed: {str(e)}")
                            st.info("Check your internet connection and try again")
                else:
                    st.error("❌ Could not find origin or destination columns")
        else:
            st.info("ℹ️ To generate geographic data, your file needs Origin and Destination columns.")
            
            # Offer to create sample data with coordinates
            st.markdown("### 📋 Sample Data with Coordinates")
            st.write("Want to see how geographic visualization works? Download this sample file:")
            
            if st.button("📁 Generate Sample Data with Coordinates"):
                sample_df = generate_sample_coordinates_file()
                sample_csv = sample_df.to_csv(index=False)
                
                st.download_button(
                    "📥 Download Sample Logistics Data with Coordinates",
                    data=sample_csv,
                    file_name="sample_logistics_with_coordinates.csv",
                    mime="text/csv",
                    help="Sample logistics manifest with geographic coordinates for testing map features"
                )
                
                st.success("✅ Sample file ready for download!")
                st.write("**Sample data includes:**")
                st.write("• 6 sample shipments")
                st.write("• Origins and destinations in major US cities") 
                st.write("• Pre-generated latitude/longitude coordinates")
                st.write("• Ready for map visualization")
                
                # Preview sample data
                with st.expander("👀 Preview sample data"):
                    st.dataframe(sample_df, use_container_width=True)

    else:
        st.info("ℹ️ Please upload a manifest file to analyze column mapping.")

with tab4:
    st.header("✅ Carrier Compliance Check")
    st.write("Ensure all carriers in your manifest are on the approved list.")
    st.markdown("The compliance check is case-insensitive.")

    if df is not None and not df.empty:
        # Try to find carrier column using mapping
        carrier_col = st.session_state.column_mapping.get('carrier')
        if not carrier_col and 'carrier' in df.columns:
            carrier_col = 'carrier'

        if carrier_col and carrier_col in df.columns:
            manifest_carriers = df[carrier_col].dropna().unique()
            approved_carriers_lower = {c.lower() for c in st.session_state.approved_carriers}

            unapproved_carriers = [
                c for c in manifest_carriers
                if str(c).lower() not in approved_carriers_lower
            ]

            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Carriers", len(manifest_carriers))
            with col2:
                st.metric("Approved", len(manifest_carriers) - len(unapproved_carriers))
            with col3:
                st.metric("Unapproved", len(unapproved_carriers))

            if unapproved_carriers:
                st.error(f"🚨 Unapproved carriers detected: {', '.join(map(str, unapproved_carriers))}")
                st.warning("Please add them to the approved list or contact a manager.")

                if st.button(f"Add {', '.join(map(str, unapproved_carriers))} to Approved List"):
                    new_carriers = [str(c) for c in unapproved_carriers]
                    st.session_state.approved_carriers.extend(new_carriers)
                    st.session_state.approved_carriers = sorted(list(set(st.session_state.approved_carriers)))
                    save_approved_carriers(st.session_state.approved_carriers)
                    st.success(f"✅ Successfully added {', '.join(new_carriers)} to the approved list.")
                    st.rerun()
            else:
                st.success("🎉 All carriers in the manifest are approved.")

            # Show carrier breakdown
            st.subheader("📊 Carrier Breakdown")
            carrier_counts = df[carrier_col].value_counts()
            st.bar_chart(carrier_counts)

        else:
            st.warning("⚠️ No carrier column found. Please check your column mapping.")

        st.markdown("---")
        st.subheader("🚚 Approved Carrier Management")
        approved_carriers_list_of_dicts = [{"Carrier Name": c} for c in st.session_state.approved_carriers]
        edited_carriers = st.data_editor(
            approved_carriers_list_of_dicts,
            num_rows="dynamic",
            use_container_width=True,
            key="approved_carriers_editor"
        )

        if st.button("Save Approved Carriers List"):
            updated_carriers = [c["Carrier Name"] for c in edited_carriers if "Carrier Name" in c and str(c["Carrier Name"]).strip()]
            st.session_state.approved_carriers = sorted(list(set(updated_carriers)))
            save_approved_carriers(st.session_state.approved_carriers)
            st.success("✅ Approved carriers list updated successfully!")
    else:
        st.info("ℹ️ Please upload a manifest file to check for carrier compliance.")

with tab5:
    st.header("🚚 Route Optimization")
    
    # Add prominent notice for enhanced data requirement
    st.info("""
    📍 **Enhanced Data Required:** This tab requires manifest data with geographic coordinates.
    
    **To use Route Optimization:**
    1. Download the **🌍 Enhanced Sample** from above, OR
    2. Upload basic data → Go to **📋 Data Mapping** → Generate coordinates → Download enhanced file → Re-upload
    
    **What you'll get:** Interactive maps, route analysis, distance calculations, and delivery optimization insights.
    """)
    show_route_optimization_tab(st.session_state.get('df', df))

with tab6:
    st.header("📥 Generate Reports")
    st.write("Export your manifest, summary, and compliance notes to an Excel file.")

    if df is not None and not df.empty:
        # Report generation options
        col1, col2 = st.columns(2)
        with col1:
            include_summary = st.checkbox("Include AI Summary", value=True)
            include_compliance = st.checkbox("Include Compliance Check", value=True)
        with col2:
            include_mapping = st.checkbox("Include Column Mapping", value=True)
            include_raw_data = st.checkbox("Include Raw Data", value=False)

        if st.button("Generate Excel Report"):
            with st.spinner("Creating comprehensive report..."):
                # Get compliance information
                compliance_notes = []
                if include_compliance:
                    carrier_col = st.session_state.column_mapping.get('carrier') or 'carrier'
                    if carrier_col in df.columns:
                        approved_carriers_lower = {c.lower() for c in st.session_state.approved_carriers}
                        manifest_carriers = df[carrier_col].dropna().unique()
                        unapproved_carriers = [
                            c for c in manifest_carriers
                            if str(c).lower() not in approved_carriers_lower
                        ]

                        if unapproved_carriers:
                            compliance_notes = [f"Unapproved carrier detected: {c}" for c in unapproved_carriers]
                        else:
                            compliance_notes = ["All carriers are approved."]
                    else:
                        compliance_notes = ["Carrier column not found for compliance check."]

                # Prepare data for export
                # Fixed function call with correct parameter names
                excel_bytes = export_manifest_to_excel(
                    df=df,
                    summary=st.session_state.get("ai_summary", "No AI summary generated.") if include_summary else None,
                    compliance_notes=compliance_notes if include_compliance else None,
                    column_mapping=st.session_state.column_mapping if include_mapping else None,
                    raw_data=st.session_state.df_original if include_raw_data else None
                )

                st.download_button(
                    "📥 Download Excel Report",
                    data=excel_bytes,
                    file_name=f"logibot_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Show report preview
                st.subheader("📝 Report Preview")

                if include_summary:
                    st.markdown("**AI Summary:**")
                    st.write(st.session_state.get("ai_summary", "No AI summary has been generated yet."))

                if include_compliance and compliance_notes:
                    st.markdown("**Compliance Notes:**")
                    for note in compliance_notes:
                        st.write(f"- {note}")

                if include_mapping and st.session_state.column_mapping:
                    st.markdown("**Column Mapping:**")
                    for standard, actual in st.session_state.column_mapping.items():
                        if actual:
                            st.write(f"- {standard.replace('_', ' ').title()}: {actual}")

                st.markdown("**Processed Data Preview:**")
                st.dataframe(df.head(), use_container_width=True)
    else:
        st.info("ℹ️ Please upload a manifest file to generate a report.")

with tab7:
    shipment_alert_tab(df)

with tab8:
    show_ai_documentation_tab()

with tab9:
    show_timeline_tab(df)


# ------------------------------------------------------------------------------
# 7. Footer Information
# ------------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>📦 LogiBot AI Copilot | Powered by OpenAI | Built with Streamlit</p>
        <p><small>Upload your logistics manifest to get started with AI-powered analysis</small></p>
    </div>
    """,
    unsafe_allow_html=True
)