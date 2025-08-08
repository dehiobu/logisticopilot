# ==============================================================================
# 🌍 Geocoding Utilities - Add Geographic Coordinates to Logistics Data
# ==============================================================================
import pandas as pd
import streamlit as st
import requests
import time
from typing import Dict, Tuple, Optional
import json

# Common city coordinates cache for faster lookups
COMMON_CITIES_COORDS = {
    # Major US Cities
    'new york': (40.7128, -74.0060),
    'new york city': (40.7128, -74.0060),
    'nyc': (40.7128, -74.0060),
    'los angeles': (34.0522, -118.2437),
    'chicago': (41.8781, -87.6298),
    'houston': (29.7604, -95.3698),
    'phoenix': (33.4484, -112.0740),
    'philadelphia': (39.9526, -75.1652),
    'san antonio': (29.4241, -98.4936),
    'san diego': (32.7157, -117.1611),
    'dallas': (32.7767, -96.7970),
    'san jose': (37.3382, -121.8863),
    'austin': (30.2672, -97.7431),
    'jacksonville': (30.3322, -81.6557),
    'fort worth': (32.7555, -97.3308),
    'columbus': (39.9612, -82.9988),
    'charlotte': (35.2271, -80.8431),
    'san francisco': (37.7749, -122.4194),
    'indianapolis': (39.7684, -86.1581),
    'seattle': (47.6062, -122.3321),
    'denver': (39.7392, -104.9903),
    'boston': (42.3601, -71.0589),
    'el paso': (31.7619, -106.4850),
    'detroit': (42.3314, -83.0458),
    'nashville': (36.1627, -86.7816),
    'portland': (45.5152, -122.6784),
    'oklahoma city': (35.4676, -97.5164),
    'las vegas': (36.1699, -115.1398),
    'louisville': (38.2527, -85.7585),
    'baltimore': (39.2904, -76.6122),
    'milwaukee': (43.0389, -87.9065),
    'albuquerque': (35.0844, -106.6504),
    'tucson': (32.2226, -110.9747),
    'fresno': (36.7378, -119.7871),
    'mesa': (33.4152, -111.8315),
    'sacramento': (38.5816, -121.4944),
    'atlanta': (33.7490, -84.3880),
    'kansas city': (39.0997, -94.5786),
    'colorado springs': (38.8339, -104.8214),
    'omaha': (41.2565, -95.9345),
    'raleigh': (35.7796, -78.6382),
    'miami': (25.7617, -80.1918),
    'cleveland': (41.4993, -81.6944),
    'tulsa': (36.1540, -95.9928),
    'oakland': (37.8044, -122.2711),
    'minneapolis': (44.9778, -93.2650),
    'wichita': (37.6872, -97.3301),
    'arlington': (32.7357, -97.1081),
    
    # Major International Cities
    'london': (51.5074, -0.1278),
    'paris': (48.8566, 2.3522),
    'berlin': (52.5200, 13.4050),
    'tokyo': (35.6762, 139.6503),
    'sydney': (-33.8688, 151.2093),
    'toronto': (43.6532, -79.3832),
    'vancouver': (49.2827, -123.1207),
    'montreal': (45.5017, -73.5673),
    'mexico city': (19.4326, -99.1332),
    'madrid': (40.4168, -3.7038),
    'rome': (41.9028, 12.4964),
    'amsterdam': (52.3676, 4.9041),
    'brussels': (50.8503, 4.3517),
    'zurich': (47.3769, 8.5417),
    'vienna': (48.2082, 16.3738),
    'stockholm': (59.3293, 18.0686),
    'copenhagen': (55.6761, 12.5683),
    'oslo': (59.9139, 10.7522),
    'dublin': (53.3498, -6.2603),
    'singapore': (1.3521, 103.8198),
    'hong kong': (22.3193, 114.1694),
    'shanghai': (31.2304, 121.4737),
    'beijing': (39.9042, 116.4074),
    'mumbai': (19.0760, 72.8777),
    'delhi': (28.7041, 77.1025),
    'bangalore': (12.9716, 77.5946),
    'seoul': (37.5665, 126.9780),
    'bangkok': (13.7563, 100.5018),
    'jakarta': (-6.2088, 106.8456),
    'manila': (14.5995, 120.9842),
    'kuala lumpur': (3.1390, 101.6869),
    'dubai': (25.2048, 55.2708),
    'istanbul': (41.0082, 28.9784),
    'cairo': (30.0444, 31.2357),
    'lagos': (6.5244, 3.3792),
    'johannesburg': (-26.2041, 28.0473),
    'cape town': (-33.9249, 18.4241),
    'sao paulo': (-23.5558, -46.6396),
    'rio de janeiro': (-22.9068, -43.1729),
    'buenos aires': (-34.6037, -58.3816),
    'lima': (-12.0464, -77.0428),
    'bogota': (4.7110, -74.0721),
    'santiago': (-33.4489, -70.6693),
}


def clean_city_name(city_name: str) -> str:
    """
    Clean and normalize city names for geocoding.
    
    Args:
        city_name (str): Raw city name
        
    Returns:
        str: Cleaned city name
    """
    if pd.isna(city_name) or city_name == '':
        return ''
    
    # Convert to string and strip whitespace
    city = str(city_name).strip().lower()
    
    # Remove common suffixes
    suffixes_to_remove = [', usa', ', us', ', united states', ', uk', ', canada']
    for suffix in suffixes_to_remove:
        if city.endswith(suffix):
            city = city[:-len(suffix)].strip()
    
    # Handle common abbreviations
    state_abbreviations = {
        'ny': 'new york',
        'la': 'los angeles',
        'sf': 'san francisco',
        'dc': 'washington',
        'philly': 'philadelphia'
    }
    
    city = state_abbreviations.get(city, city)
    
    return city


def get_coordinates_from_cache(city_name: str) -> Optional[Tuple[float, float]]:
    """
    Get coordinates from the cache of common cities.
    
    Args:
        city_name (str): City name to look up
        
    Returns:
        Optional[Tuple[float, float]]: (latitude, longitude) or None if not found
    """
    clean_city = clean_city_name(city_name)
    return COMMON_CITIES_COORDS.get(clean_city)


def geocode_with_nominatim(city_name: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a city name using OpenStreetMap's Nominatim service (free).
    
    Args:
        city_name (str): City name to geocode
        
    Returns:
        Optional[Tuple[float, float]]: (latitude, longitude) or None if not found
    """
    try:
        # Clean the city name
        clean_city = clean_city_name(city_name)
        if not clean_city:
            return None
        
        # Nominatim API endpoint
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': clean_city,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        # Add user agent (required by Nominatim)
        headers = {
            'User-Agent': 'LogiBot-Logistics-App/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return (lat, lon)
        
        return None
        
    except Exception as e:
        st.warning(f"Geocoding failed for {city_name}: {str(e)}")
        return None


def add_geographic_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add latitude and longitude coordinates for Origin and Destination columns.
    
    Args:
        df (pd.DataFrame): DataFrame with Origin and Destination columns
        
    Returns:
        pd.DataFrame: DataFrame with added coordinate columns
    """
    df_with_coords = df.copy()
    
    # Check if required columns exist
    origin_col = None
    dest_col = None
    
    # Case-insensitive search for origin and destination columns
    for col in df.columns:
        col_lower = col.lower()
        if 'origin' in col_lower:
            origin_col = col
        elif 'destination' in col_lower or 'dest' in col_lower:
            dest_col = col
    
    if not origin_col or not dest_col:
        st.error("Could not find Origin and Destination columns in the data.")
        return df
    
    # Initialize coordinate columns
    df_with_coords['Origin Lat'] = None
    df_with_coords['Origin Lon'] = None
    df_with_coords['Dest Lat'] = None
    df_with_coords['Dest Lon'] = None
    
    # Get unique cities to minimize API calls
    unique_origins = df[origin_col].dropna().unique()
    unique_destinations = df[dest_col].dropna().unique()
    all_unique_cities = set(list(unique_origins) + list(unique_destinations))
    
    # Progress tracking
    total_cities = len(all_unique_cities)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Geocode all unique cities
    city_coordinates = {}
    
    for i, city in enumerate(all_unique_cities):
        status_text.text(f"Geocoding {city} ({i+1}/{total_cities})...")
        
        # First try cache
        coords = get_coordinates_from_cache(city)
        
        # If not in cache, try geocoding service
        if coords is None:
            coords = geocode_with_nominatim(city)
            # Rate limiting to be respectful to free service
            time.sleep(1)  # 1 second delay between requests
        
        if coords:
            city_coordinates[city] = coords
        else:
            st.warning(f"Could not geocode: {city}")
        
        progress_bar.progress((i + 1) / total_cities)
    
    # Apply coordinates to DataFrame
    for idx, row in df_with_coords.iterrows():
        origin_city = row[origin_col]
        dest_city = row[dest_col]
        
        # Origin coordinates
        if origin_city in city_coordinates:
            lat, lon = city_coordinates[origin_city]
            df_with_coords.at[idx, 'Origin Lat'] = lat
            df_with_coords.at[idx, 'Origin Lon'] = lon
        
        # Destination coordinates
        if dest_city in city_coordinates:
            lat, lon = city_coordinates[dest_city]
            df_with_coords.at[idx, 'Dest Lat'] = lat
            df_with_coords.at[idx, 'Dest Lon'] = lon
    
    progress_bar.empty()
    status_text.empty()
    
    # Show summary
    successful_origins = df_with_coords['Origin Lat'].notna().sum()
    successful_destinations = df_with_coords['Dest Lat'].notna().sum()
    total_rows = len(df_with_coords)
    
    st.success(f"✅ Geocoding complete!")
    st.info(f"📍 Successfully geocoded {successful_origins}/{total_rows} origins and {successful_destinations}/{total_rows} destinations")
    
    return df_with_coords


def generate_sample_coordinates_file():
    """
    Generate a sample CSV file with coordinates for testing.
    """
    sample_data = {
        'Shipment ID': ['SHP001', 'SHP002', 'SHP003', 'SHP004', 'SHP005', 'SHP006'],
        'Carrier': ['DPD', 'FedEx', 'DHL', 'XYZ Express', 'DPD', 'UPS'],
        'Status': ['Delivered', 'In Transit', 'Delayed', 'Cancelled', 'Delivered', 'Delayed'],
        'Cost': [12.5, 48, 15.75, 99.99, 13, 20],
        'Tracking Ref': ['TR001', 'TR002', 'TR003', 'TR004', 'TR005', 'TR006'],
        'Origin': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Boston', 'Seattle'],
        'Destination': ['Miami', 'Denver', 'Atlanta', 'Phoenix', 'Dallas', 'Portland'],
        'Origin Lat': [40.7128, 34.0522, 41.8781, 29.7604, 42.3601, 47.6062],
        'Origin Lon': [-74.0060, -118.2437, -87.6298, -95.3698, -71.0589, -122.3321],
        'Dest Lat': [25.7617, 39.7392, 33.7490, 33.4484, 32.7767, 45.5152],
        'Dest Lon': [-80.1918, -104.9903, -84.3880, -112.0740, -96.7970, -122.6784]
    }
    
    sample_df = pd.DataFrame(sample_data)
    return sample_df


def validate_geographic_data(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame has all required geographic columns with valid data.
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        
    Returns:
        bool: True if valid geographic data exists
    """
    required_columns = ['Origin Lat', 'Origin Lon', 'Dest Lat', 'Dest Lon']
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False
    
    # Check if we have valid coordinate data
    valid_origins = df[['Origin Lat', 'Origin Lon']].notna().all(axis=1).sum()
    valid_destinations = df[['Dest Lat', 'Dest Lon']].notna().all(axis=1).sum()
    
    # At least 50% of rows should have valid coordinates
    threshold = len(df) * 0.5
    
    return valid_origins >= threshold and valid_destinations >= threshold