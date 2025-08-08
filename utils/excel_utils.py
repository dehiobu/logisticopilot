import pandas as pd
import io
import os
import xlsxwriter # Explicitly import xlsxwriter, which Pandas uses as an engine for .xlsx files
from datetime import datetime
from typing import Optional, List, Dict, Any


def export_manifest_to_excel(
    df: pd.DataFrame, 
    summary: str = None, 
    compliance_notes: list = None,
    column_mapping: dict = None,
    raw_data: pd.DataFrame = None,
    **kwargs
) -> bytes:
    """
    Exports the logistics manifest DataFrame, AI-generated summary, and optional compliance notes
    into a multi-sheet Excel workbook. The entire workbook is created in-memory and returned
    as a bytes object, suitable for direct download in web applications like Streamlit.

    Args:
        df (pd.DataFrame): The pandas DataFrame containing the logistics manifest data.
        summary (str, optional): A string containing the AI-generated summary of the manifest.
        compliance_notes (list, optional): A list of strings, where each string represents a compliance issue.
                                   If None or empty, a sheet indicating "No concerns" is created.
        column_mapping (Dict[str, str], optional): Mapping of standard fields to actual column names.
        raw_data (pd.DataFrame, optional): Original raw data before processing.
        **kwargs: Additional keyword arguments for backward compatibility.

    Returns:
        bytes: The complete content of the generated Excel file as a bytes object.
    """
    # Handle the case where the function is called with the old signature
    # export_manifest_to_excel(processed_data=df, summary=summary, ...)
    if 'processed_data' in kwargs:
        df = kwargs['processed_data']
    
    # Create an in-memory binary stream (BytesIO object) to act as a file.
    # The Excel file will be written to this stream instead of a physical file on disk.
    output = io.BytesIO()
    
    # Initialize Pandas ExcelWriter, specifying the BytesIO object as the path
    # and 'xlsxwriter' as the engine. This tells Pandas to write the Excel data
    # into our in-memory stream using the xlsxwriter library.
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # Get the workbook and add some formatting
    workbook = writer.book
    
    # Define some formats for better presentation
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#366092',
        'font_color': 'white',
        'border': 1
    })
    
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'fg_color': '#D7E4BD',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'border': 1,
        'text_wrap': True,
        'valign': 'top'
    })

    # --- Sheet 1: Executive Summary ---
    # Create an executive summary sheet with key metrics
    summary_data = []
    summary_data.append(['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    summary_data.append(['Total Shipments', len(df)])
    summary_data.append(['Total Columns', len(df.columns)])
    
    # Add carrier and status info if available
    if 'Carrier' in df.columns:
        summary_data.append(['Unique Carriers', df['Carrier'].nunique()])
        top_carrier = df['Carrier'].value_counts().index[0] if len(df['Carrier'].value_counts()) > 0 else 'N/A'
        summary_data.append(['Top Carrier', top_carrier])
    
    if 'Status' in df.columns:
        summary_data.append(['Unique Status Types', df['Status'].nunique()])
        most_common_status = df['Status'].value_counts().index[0] if len(df['Status'].value_counts()) > 0 else 'N/A'
        summary_data.append(['Most Common Status', most_common_status])
    
    if 'Cost' in df.columns and pd.api.types.is_numeric_dtype(df['Cost']):
        summary_data.append(['Total Cost', f"${df['Cost'].sum():.2f}"])
        summary_data.append(['Average Cost', f"${df['Cost'].mean():.2f}"])
    
    summary_overview_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
    summary_overview_df.to_excel(writer, sheet_name='Executive Summary', index=False, startrow=1)
    
    # Get the summary worksheet for formatting
    summary_worksheet = writer.sheets['Executive Summary']
    summary_worksheet.write('A1', '📦 LogiBot Report Summary', title_format)
    
    # Format the summary sheet
    summary_worksheet.set_column('A:A', 25, cell_format)
    summary_worksheet.set_column('B:B', 30, cell_format)
    for row_num in range(2, len(summary_data) + 2):
        summary_worksheet.set_row(row_num, None, cell_format)

    # --- Sheet 2: Manifest Data ---
    # Write the main logistics manifest DataFrame to the second sheet.
    df.to_excel(writer, sheet_name='Manifest Data', index=False)
    
    # Get the manifest worksheet for formatting
    manifest_worksheet = writer.sheets['Manifest Data']
    
    # Format headers
    for col_num, column_name in enumerate(df.columns):
        manifest_worksheet.write(0, col_num, column_name, header_format)
    
    # Auto-adjust column widths based on content
    for i, column in enumerate(df.columns):
        column_width = max(
            df[column].astype(str).map(len).max(),  # Max content width
            len(column)  # Header width
        ) + 2  # Add some padding
        column_width = min(column_width, 50)  # Cap at 50 characters
        manifest_worksheet.set_column(i, i, column_width, cell_format)

    # --- Sheet 3: AI Summary ---
    if summary and summary.strip() and summary != "No AI summary generated.":
        # Create a DataFrame from the AI-generated summary string.
        summary_df = pd.DataFrame([summary], columns=['AI Manifest Summary'])
        summary_df.to_excel(writer, sheet_name='AI Summary', index=False)
        
        # Format the AI summary sheet
        ai_worksheet = writer.sheets['AI Summary']
        ai_worksheet.write(0, 0, 'AI Manifest Summary', header_format)
        ai_worksheet.set_column('A:A', 80, cell_format)
        ai_worksheet.set_row(1, 100, cell_format)  # Make the summary row taller
    else:
        # Create a sheet indicating no AI summary is available
        no_summary_df = pd.DataFrame(["No AI summary has been generated yet. Use the 'AI Insights' tab to generate one."], 
                                   columns=['AI Manifest Summary'])
        no_summary_df.to_excel(writer, sheet_name='AI Summary', index=False)
        
        # Format the sheet
        ai_worksheet = writer.sheets['AI Summary']
        ai_worksheet.write(0, 0, 'AI Manifest Summary', header_format)
        ai_worksheet.set_column('A:A', 60, cell_format)

    # --- Sheet 4: Compliance Notes ---
    # Check if there are any compliance notes to write.
    if compliance_notes and len(compliance_notes) > 0:
        # If notes exist, create a DataFrame from the list of notes.
        compliance_df = pd.DataFrame(compliance_notes, columns=['Compliance Concerns'])
        compliance_df.to_excel(writer, sheet_name='Compliance Notes', index=False)
        
        # Format the compliance sheet
        compliance_worksheet = writer.sheets['Compliance Notes']
        compliance_worksheet.write(0, 0, 'Compliance Concerns', header_format)
        compliance_worksheet.set_column('A:A', 60, cell_format)
        
        # Color code the compliance notes
        warning_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#FFE6E6'  # Light red background for warnings
        })
        
        success_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#E6FFE6'  # Light green background for success
        })
        
        # Apply conditional formatting based on content
        for i, note in enumerate(compliance_notes, 1):
            if any(word in note.lower() for word in ['unapproved', 'warning', 'error', 'concern', '⚠️', '🚨']):
                compliance_worksheet.set_row(i, 20, warning_format)
            elif any(word in note.lower() for word in ['approved', 'success', 'good', 'compliant', '✅']):
                compliance_worksheet.set_row(i, 20, success_format)
            else:
                compliance_worksheet.set_row(i, 20, cell_format)
    else:
        # If no compliance notes are provided, create a sheet indicating no concerns.
        no_notes_df = pd.DataFrame(["✅ No compliance concerns identified."], columns=['Compliance Concerns'])
        no_notes_df.to_excel(writer, sheet_name='Compliance Notes', index=False)
        
        # Format the sheet
        compliance_worksheet = writer.sheets['Compliance Notes']
        compliance_worksheet.write(0, 0, 'Compliance Concerns', header_format)
        compliance_worksheet.set_column('A:A', 50, cell_format)
        
        # Green background for success
        success_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#E6FFE6'
        })
        compliance_worksheet.set_row(1, 20, success_format)

    # --- Sheet 5: Column Mapping (if provided) ---
    if column_mapping:
        mapping_data = []
        for standard_field, actual_column in column_mapping.items():
            if actual_column:
                mapping_data.append([
                    standard_field.replace('_', ' ').title(),
                    actual_column,
                    "✅ Mapped"
                ])
        
        if mapping_data:
            mapping_df = pd.DataFrame(mapping_data, columns=['Standard Field', 'Your Column', 'Status'])
            mapping_df.to_excel(writer, sheet_name='Column Mapping', index=False)
            
            # Format the mapping sheet
            mapping_worksheet = writer.sheets['Column Mapping']
            for col_num, column_name in enumerate(['Standard Field', 'Your Column', 'Status']):
                mapping_worksheet.write(0, col_num, column_name, header_format)
            
            mapping_worksheet.set_column('A:A', 25, cell_format)
            mapping_worksheet.set_column('B:B', 25, cell_format)
            mapping_worksheet.set_column('C:C', 15, cell_format)

    # --- Sheet 6: Analytics (if we have the right data) ---
    if 'Carrier' in df.columns:
        analytics_data = []
        
        # Carrier distribution
        carrier_counts = df['Carrier'].value_counts()
        total_shipments = len(df)
        
        analytics_data.append(['=== CARRIER ANALYSIS ===', '', ''])
        analytics_data.append(['Carrier', 'Shipments', 'Percentage'])
        
        for carrier, count in carrier_counts.items():
            percentage = f"{(count/total_shipments)*100:.1f}%"
            analytics_data.append([carrier, count, percentage])
        
        # Status distribution if available
        if 'Status' in df.columns:
            analytics_data.append(['', '', ''])  # Empty row
            analytics_data.append(['=== STATUS ANALYSIS ===', '', ''])
            analytics_data.append(['Status', 'Count', 'Percentage'])
            
            status_counts = df['Status'].value_counts()
            for status, count in status_counts.items():
                percentage = f"{(count/total_shipments)*100:.1f}%"
                analytics_data.append([status, count, percentage])
        
        if analytics_data:
            analytics_df = pd.DataFrame(analytics_data, columns=['Category', 'Count', 'Percentage'])
            analytics_df.to_excel(writer, sheet_name='Analytics', index=False)
            
            # Format the analytics sheet
            analytics_worksheet = writer.sheets['Analytics']
            analytics_worksheet.write(0, 0, 'Category', header_format)
            analytics_worksheet.write(0, 1, 'Count', header_format)
            analytics_worksheet.write(0, 2, 'Percentage', header_format)
            
            analytics_worksheet.set_column('A:A', 30, cell_format)
            analytics_worksheet.set_column('B:B', 15, cell_format)
            analytics_worksheet.set_column('C:C', 15, cell_format)

    # --- Sheet 7: Raw Data (if provided) ---
    if raw_data is not None:
        raw_data.to_excel(writer, sheet_name='Raw Data', index=False)
        
        # Format the raw data sheet
        raw_worksheet = writer.sheets['Raw Data']
        
        # Format headers
        for col_num, column_name in enumerate(raw_data.columns):
            raw_worksheet.write(0, col_num, column_name, header_format)
        
        # Auto-adjust column widths
        for i, column in enumerate(raw_data.columns):
            column_width = max(
                raw_data[column].astype(str).map(len).max(),
                len(column)
            ) + 2
            column_width = min(column_width, 50)
            raw_worksheet.set_column(i, i, column_width, cell_format)

    # --- Finalize the Excel File ---
    # Close the Pandas Excel writer. This is a crucial step that finalizes the Excel file
    # structure and writes all buffered data into the 'output' BytesIO stream.
    writer.close()
    
    # Rewind the BytesIO stream to the beginning. After writing, the stream's "pointer"
    # is at the end of the data. We need to move it to the start to read its content.
    output.seek(0)
    
    # Read the entire content of the BytesIO stream and return it as a bytes object.
    # This bytes object can then be directly passed to Streamlit's st.download_button.
    return output.getvalue()


def create_basic_excel_export(df: pd.DataFrame) -> bytes:
    """
    Create a basic Excel export with just the data.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        
    Returns:
        bytes: Excel file as bytes
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Data']
        
        # Add some basic formatting
        header_format = workbook.add_format({
            'bold': True,
            'fg_color': '#366092',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({'border': 1})
        
        # Format headers
        for col_num, column_name in enumerate(df.columns):
            worksheet.write(0, col_num, column_name, header_format)
        
        # Auto-adjust column widths
        for i, column in enumerate(df.columns):
            column_width = max(
                df[column].astype(str).map(len).max(),
                len(column)
            ) + 2
            column_width = min(column_width, 50)
            worksheet.set_column(i, i, column_width, cell_format)
    
    output.seek(0)
    return output.getvalue()


def export_to_csv(df: pd.DataFrame) -> str:
    """
    Export DataFrame to CSV string.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        
    Returns:
        str: CSV data as string
    """
    return df.to_csv(index=False)


def export_to_json(df: pd.DataFrame) -> str:
    """
    Export DataFrame to JSON string.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        
    Returns:
        str: JSON data as string
    """
    return df.to_json(orient='records', indent=2)