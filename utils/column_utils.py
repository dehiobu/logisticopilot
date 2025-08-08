# ==============================================================================
# 📊 Column Utilities - Data Column Management and Validation
# ==============================================================================
import pandas as pd
import streamlit as st
from typing import List, Dict, Optional, Tuple


# Standard column mappings for logistics manifests
STANDARD_COLUMNS = {
    'shipment_id': ['shipment_id', 'shipment id', 'id', 'tracking_number', 'tracking number'],
    'carrier': ['carrier', 'carrier_name', 'carrier name', 'shipping_company', 'shipping company'],
    'origin': ['origin', 'origin_city', 'origin city', 'from', 'pickup_location', 'pickup location'],
    'destination': ['destination', 'destination_city', 'destination city', 'to', 'delivery_location', 'delivery location'],
    'weight': ['weight', 'weight_kg', 'weight kg', 'total_weight', 'total weight'],
    'status': ['status', 'shipment_status', 'shipment status', 'delivery_status', 'delivery status'],
    'date': ['date', 'ship_date', 'ship date', 'pickup_date', 'pickup date', 'created_date', 'created date'],
    'delivery_date': ['delivery_date', 'delivery date', 'expected_delivery', 'expected delivery', 'eta'],
    'cost': ['cost', 'shipping_cost', 'shipping cost', 'price', 'amount', 'total_cost', 'total cost'],
    'priority': ['priority', 'priority_level', 'priority level', 'urgency', 'service_level', 'service level']
}


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to lowercase and replace spaces/special chars with underscores.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with normalized column names
    """
    df_copy = df.copy()
    df_copy.columns = df_copy.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
    return df_copy


def detect_column_mapping(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Automatically detect which columns in the DataFrame correspond to standard logistics fields.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        Dict[str, Optional[str]]: Mapping of standard column names to actual column names
    """
    mapping = {}
    df_columns_lower = [col.lower() for col in df.columns]
    
    for standard_col, possible_names in STANDARD_COLUMNS.items():
        mapped_col = None
        for possible_name in possible_names:
            if possible_name in df_columns_lower:
                # Find the actual column name (preserving original case)
                actual_col_idx = df_columns_lower.index(possible_name)
                mapped_col = df.columns[actual_col_idx]
                break
        mapping[standard_col] = mapped_col
    
    return mapping


def validate_required_columns(df: pd.DataFrame, required_columns: List[str] = None) -> Tuple[bool, List[str]]:
    """
    Validate that the DataFrame contains required columns for logistics operations.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        required_columns (List[str]): List of required column names. If None, uses default set.
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_missing_columns)
    """
    if required_columns is None:
        required_columns = ['carrier', 'origin', 'destination']
    
    column_mapping = detect_column_mapping(df)
    missing_columns = []
    
    for req_col in required_columns:
        if column_mapping.get(req_col) is None:
            missing_columns.append(req_col)
    
    return len(missing_columns) == 0, missing_columns


def get_column_suggestions(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Get suggestions for unmapped columns based on similarity.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        Dict[str, List[str]]: Suggestions for each standard column
    """
    suggestions = {}
    df_columns_lower = [col.lower() for col in df.columns]
    
    for standard_col, possible_names in STANDARD_COLUMNS.items():
        column_suggestions = []
        for df_col in df.columns:
            df_col_lower = df_col.lower()
            # Check for partial matches
            for possible_name in possible_names:
                if possible_name in df_col_lower or df_col_lower in possible_name:
                    if df_col not in column_suggestions:
                        column_suggestions.append(df_col)
        
        suggestions[standard_col] = column_suggestions[:3]  # Limit to top 3 suggestions
    
    return suggestions


def create_column_mapping_interface(df: pd.DataFrame) -> Dict[str, str]:
    """
    Create a Streamlit interface for manual column mapping.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        Dict[str, str]: User-selected column mapping
    """
    st.subheader("📋 Column Mapping")
    st.write("Map your data columns to standard logistics fields:")
    
    auto_mapping = detect_column_mapping(df)
    user_mapping = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Standard Fields:**")
        for standard_col in STANDARD_COLUMNS.keys():
            st.write(f"• {standard_col.replace('_', ' ').title()}")
    
    with col2:
        st.write("**Your Columns:**")
        for col in df.columns:
            st.write(f"• {col}")
    
    st.markdown("---")
    
    # Create selectboxes for mapping
    for standard_col in STANDARD_COLUMNS.keys():
        auto_detected = auto_mapping.get(standard_col)
        options = ["(Not mapped)"] + list(df.columns)
        
        if auto_detected:
            default_idx = options.index(auto_detected) if auto_detected in options else 0
        else:
            default_idx = 0
        
        selected = st.selectbox(
            f"Map '{standard_col.replace('_', ' ').title()}' to:",
            options,
            index=default_idx,
            key=f"mapping_{standard_col}"
        )
        
        if selected != "(Not mapped)":
            user_mapping[standard_col] = selected
    
    return user_mapping


def apply_column_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Apply column mapping to rename columns according to standard names.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        mapping (Dict[str, str]): Column mapping dictionary
        
    Returns:
        pd.DataFrame: DataFrame with renamed columns
    """
    df_mapped = df.copy()
    rename_dict = {v: k for k, v in mapping.items() if v in df.columns}
    df_mapped = df_mapped.rename(columns=rename_dict)
    return df_mapped


def get_column_info(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Get detailed information about each column in the DataFrame.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        Dict[str, Dict]: Column information including type, null count, unique values, etc.
    """
    column_info = {}
    
    for col in df.columns:
        info = {
            'dtype': str(df[col].dtype),
            'null_count': df[col].isnull().sum(),
            'null_percentage': (df[col].isnull().sum() / len(df)) * 100,
            'unique_count': df[col].nunique(),
            'sample_values': df[col].dropna().head(3).tolist()
        }
        
        # Add specific info for numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            info.update({
                'min_value': df[col].min(),
                'max_value': df[col].max(),
                'mean_value': df[col].mean()
            })
        
        column_info[col] = info
    
    return column_info


def display_column_analysis(df: pd.DataFrame):
    """
    Display a comprehensive analysis of the DataFrame columns in Streamlit.
    
    Args:
        df (pd.DataFrame): Input DataFrame
    """
    st.subheader("📊 Column Analysis")
    
    column_info = get_column_info(df)
    mapping = detect_column_mapping(df)
    
    # Create a summary table
    summary_data = []
    for col in df.columns:
        info = column_info[col]
        # Find if this column is mapped to a standard field
        mapped_to = None
        for standard_col, actual_col in mapping.items():
            if actual_col == col:
                mapped_to = standard_col.replace('_', ' ').title()
                break
        
        summary_data.append({
            'Column': col,
            'Type': info['dtype'],
            'Nulls': f"{info['null_count']} ({info['null_percentage']:.1f}%)",
            'Unique': info['unique_count'],
            'Mapped To': mapped_to or 'Not mapped',
            'Sample Values': ', '.join(map(str, info['sample_values'][:2]))
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
    
    # Show validation results
    is_valid, missing = validate_required_columns(df)
    if is_valid:
        st.success("✅ All required columns detected!")
    else:
        st.warning(f"⚠️ Missing required columns: {', '.join(missing)}")
        
        # Show suggestions
        suggestions = get_column_suggestions(df)
        for missing_col in missing:
            if suggestions.get(missing_col):
                st.info(f"💡 Suggestions for '{missing_col}': {', '.join(suggestions[missing_col])}")


def clean_column_data(df: pd.DataFrame, column_mapping: Dict[str, str] = None) -> pd.DataFrame:
    """
    Clean and standardize data in mapped columns.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        column_mapping (Dict[str, str]): Column mapping dictionary
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_clean = df.copy()
    
    if column_mapping is None:
        column_mapping = detect_column_mapping(df)
    
    # Clean carrier names
    if column_mapping.get('carrier'):
        carrier_col = column_mapping['carrier']
        df_clean[carrier_col] = df_clean[carrier_col].str.strip().str.title()
    
    # Clean status values
    if column_mapping.get('status'):
        status_col = column_mapping['status']
        df_clean[status_col] = df_clean[status_col].str.strip().str.lower()
    
    # Clean location names
    for loc_col in ['origin', 'destination']:
        if column_mapping.get(loc_col):
            col_name = column_mapping[loc_col]
            df_clean[col_name] = df_clean[col_name].str.strip().str.title()
    
    # Convert numeric columns
    for num_col in ['weight', 'cost']:
        if column_mapping.get(num_col):
            col_name = column_mapping[num_col]
            df_clean[col_name] = pd.to_numeric(df_clean[col_name], errors='coerce')
    
    # Convert date columns
    for date_col in ['date', 'delivery_date']:
        if column_mapping.get(date_col):
            col_name = column_mapping[date_col]
            df_clean[col_name] = pd.to_datetime(df_clean[col_name], errors='coerce')
    
    return df_clean


# ==============================================================================
# 🏗️ ColumnMapper Class - Comprehensive Version with All Methods
# ==============================================================================

class ColumnMapper:
    """
    A comprehensive class to handle column mapping operations for dashboard and other tabs.
    This provides backward compatibility with existing code and includes all functionality.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the ColumnMapper with a DataFrame.
        
        Args:
            df (pd.DataFrame): The DataFrame to analyze
        """
        self.df = df
        self.mapping = detect_column_mapping(df)
        self.standard_columns = STANDARD_COLUMNS
    
    @staticmethod
    def get_display_name(column_name: str) -> str:
        """
        Convert a column name to a user-friendly display name.
        
        Args:
            column_name (str): Original column name
            
        Returns:
            str: Display-friendly column name
        """
        if not column_name:
            return ""
        
        # Replace underscores and hyphens with spaces
        display_name = column_name.replace('_', ' ').replace('-', ' ')
        
        # Title case each word
        display_name = ' '.join(word.capitalize() for word in display_name.split())
        
        # Handle common abbreviations
        abbreviations = {
            'Id': 'ID',
            'Eta': 'ETA',
            'Kg': 'KG',
            'Lb': 'LB',
            'Lbs': 'LBS',
            'Usd': 'USD',
            'Api': 'API',
            'Url': 'URL',
            'Sms': 'SMS',
            'Gps': 'GPS'
        }
        
        for abbr, replacement in abbreviations.items():
            display_name = display_name.replace(abbr, replacement)
        
        return display_name
    
    @staticmethod
    def get_column_if_exists(df: pd.DataFrame, standard_name: str) -> Optional[str]:
        """
        Get the actual column name for a standard field if it exists.
        
        Args:
            df (pd.DataFrame): DataFrame to check
            standard_name (str): Standard column name (e.g., 'carrier', 'origin')
            
        Returns:
            Optional[str]: Actual column name or None if not found
        """
        mapping = detect_column_mapping(df)
        return mapping.get(standard_name)
    
    @staticmethod
    def format_column_names(df: pd.DataFrame) -> List[str]:
        """
        Format all column names for display.
        
        Args:
            df (pd.DataFrame): DataFrame with columns to format
            
        Returns:
            List[str]: List of formatted column names
        """
        return [ColumnMapper.get_display_name(col) for col in df.columns]
    
    def get_mapping(self) -> Dict[str, Optional[str]]:
        """Get the current column mapping."""
        return self.mapping
    
    def update_mapping(self, new_mapping: Dict[str, str]):
        """Update the column mapping."""
        self.mapping.update(new_mapping)
    
    def get_column(self, standard_name: str) -> Optional[str]:
        """
        Get the actual column name for a standard field.
        
        Args:
            standard_name (str): Standard column name (e.g., 'carrier', 'origin')
            
        Returns:
            Optional[str]: Actual column name or None if not found
        """
        return self.mapping.get(standard_name)
    
    def has_column(self, standard_name: str) -> bool:
        """Check if a standard column is mapped."""
        return self.mapping.get(standard_name) is not None
    
    def get_mapped_columns(self) -> List[str]:
        """Get list of all mapped column names."""
        return [col for col in self.mapping.values() if col is not None]
    
    def get_unmapped_columns(self) -> List[str]:
        """Get list of DataFrame columns that aren't mapped."""
        mapped_cols = set(self.get_mapped_columns())
        return [col for col in self.df.columns if col not in mapped_cols]
    
    def validate_required_columns(self, required: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate that required columns are present.
        
        Args:
            required (List[str]): List of required standard column names
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, missing_columns)
        """
        if required is None:
            required = ['carrier', 'origin', 'destination']
        
        missing = [col for col in required if not self.has_column(col)]
        return len(missing) == 0, missing
    
    def apply_mapping(self) -> pd.DataFrame:
        """Apply the current mapping to create a standardized DataFrame."""
        return apply_column_mapping(self.df, self.mapping)
    
    def clean_data(self) -> pd.DataFrame:
        """Clean and standardize the mapped data."""
        return clean_column_data(self.df, self.mapping)
    
    def get_column_info(self) -> Dict[str, Dict]:
        """Get detailed information about mapped columns."""
        return get_column_info(self.df)
    
    def display_analysis(self):
        """Display column analysis in Streamlit."""
        display_column_analysis(self.df)
    
    def create_mapping_interface(self) -> Dict[str, str]:
        """Create Streamlit interface for column mapping."""
        return create_column_mapping_interface(self.df)
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> 'ColumnMapper':
        """Create a ColumnMapper instance from a DataFrame."""
        return cls(df)
    
    def get_standard_field_for_column(self, column_name: str) -> Optional[str]:
        """
        Get the standard field name that a column is mapped to.
        
        Args:
            column_name (str): The actual column name in the DataFrame
            
        Returns:
            Optional[str]: Standard field name or None if not mapped
        """
        for standard_field, actual_column in self.mapping.items():
            if actual_column == column_name:
                return standard_field
        return None
    
    def is_numeric_column(self, column_name: str) -> bool:
        """
        Check if a column contains numeric data.
        
        Args:
            column_name (str): Column name to check
            
        Returns:
            bool: True if column is numeric
        """
        if column_name not in self.df.columns:
            return False
        return pd.api.types.is_numeric_dtype(self.df[column_name])
    
    def is_datetime_column(self, column_name: str) -> bool:
        """
        Check if a column contains datetime data.
        
        Args:
            column_name (str): Column name to check
            
        Returns:
            bool: True if column is datetime
        """
        if column_name not in self.df.columns:
            return False
        return pd.api.types.is_datetime64_any_dtype(self.df[column_name])
    
    def get_column_summary(self, column_name: str) -> Dict:
        """
        Get a summary of a specific column.
        
        Args:
            column_name (str): Column name to summarize
            
        Returns:
            Dict: Column summary information
        """
        if column_name not in self.df.columns:
            return {}
        
        col_data = self.df[column_name]
        summary = {
            'name': column_name,
            'display_name': self.get_display_name(column_name),
            'dtype': str(col_data.dtype),
            'count': len(col_data),
            'null_count': col_data.isnull().sum(),
            'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
            'unique_count': col_data.nunique(),
            'is_numeric': self.is_numeric_column(column_name),
            'is_datetime': self.is_datetime_column(column_name),
            'standard_field': self.get_standard_field_for_column(column_name)
        }
        
        if summary['is_numeric']:
            summary.update({
                'min': col_data.min(),
                'max': col_data.max(),
                'mean': col_data.mean(),
                'median': col_data.median()
            })
        
        if summary['unique_count'] <= 20:  # Show unique values for categorical data
            summary['unique_values'] = col_data.value_counts().to_dict()
        
        return summary
    
    # Additional methods for extended functionality from original
    def get_suggestions_for_unmapped(self) -> Dict[str, List[str]]:
        """Get suggestions for unmapped standard columns."""
        return get_column_suggestions(self.df)
    
    def auto_detect_and_update_mapping(self):
        """Re-detect column mapping and update current mapping."""
        self.mapping = detect_column_mapping(self.df)
    
    def export_mapping_config(self) -> Dict:
        """Export current mapping configuration for saving/loading."""
        return {
            'mapping': self.mapping,
            'df_columns': list(self.df.columns),
            'standard_columns': self.standard_columns
        }
    
    def import_mapping_config(self, config: Dict):
        """Import mapping configuration from saved config."""
        if 'mapping' in config:
            # Validate that the columns still exist in the DataFrame
            valid_mapping = {}
            for standard, actual in config['mapping'].items():
                if actual is None or actual in self.df.columns:
                    valid_mapping[standard] = actual
            self.mapping = valid_mapping
    
    def get_data_quality_report(self) -> Dict[str, Dict]:
        """Generate a comprehensive data quality report."""
        report = {}
        
        for standard_field, actual_column in self.mapping.items():
            if actual_column is not None:
                col_summary = self.get_column_summary(actual_column)
                
                # Add quality metrics
                col_data = self.df[actual_column]
                quality_metrics = {
                    'completeness': (1 - col_summary['null_percentage'] / 100) * 100,
                    'uniqueness': (col_summary['unique_count'] / len(col_data)) * 100 if len(col_data) > 0 else 0,
                    'has_duplicates': col_summary['unique_count'] < len(col_data),
                    'data_type_consistency': True,  # Could be enhanced with more complex checks
                    'contains_outliers': False  # Could be enhanced with statistical outlier detection
                }
                
                # Enhanced outlier detection for numeric columns
                if col_summary['is_numeric'] and col_summary['unique_count'] > 1:
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                    quality_metrics['contains_outliers'] = len(outliers) > 0
                    quality_metrics['outlier_count'] = len(outliers)
                
                col_summary.update(quality_metrics)
                report[standard_field] = col_summary
        
        return report
    
    def generate_mapping_suggestions(self) -> Dict[str, List[Tuple[str, float]]]:
        """Generate weighted suggestions for column mapping based on similarity scores."""
        suggestions = {}
        
        for standard_field, possible_names in STANDARD_COLUMNS.items():
            if self.mapping.get(standard_field) is None:  # Only for unmapped fields
                column_scores = []
                
                for df_col in self.df.columns:
                    df_col_lower = df_col.lower()
                    max_score = 0
                    
                    for possible_name in possible_names:
                        # Exact match
                        if df_col_lower == possible_name:
                            score = 1.0
                        # Contains match
                        elif possible_name in df_col_lower:
                            score = 0.8
                        # Partial match
                        elif any(part in df_col_lower for part in possible_name.split()):
                            score = 0.6
                        # Similar words
                        elif df_col_lower in possible_name:
                            score = 0.4
                        else:
                            score = 0
                        
                        max_score = max(max_score, score)
                    
                    if max_score > 0:
                        column_scores.append((df_col, max_score))
                
                # Sort by score and take top 3
                column_scores.sort(key=lambda x: x[1], reverse=True)
                suggestions[standard_field] = column_scores[:3]
        
        return suggestions