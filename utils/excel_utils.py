import pandas as pd # Import the pandas library, commonly used for data manipulation and analysis, especially with DataFrames.
from openpyxl import Workbook # Import Workbook from openpyxl, used to create new Excel workbooks.
from openpyxl.utils.dataframe import dataframe_to_rows # Import dataframe_to_rows to convert pandas DataFrames into rows suitable for openpyxl.
from openpyxl.styles import Font # Import Font from openpyxl.styles to apply font formatting (e.g., bold).
from datetime import datetime # Import datetime from the datetime module to generate dynamic timestamps for filenames.

def export_manifest_to_excel(df, summary_text, compliance_notes=None):
    """
    Exports a logistics manifest DataFrame, AI-generated summary, and optional compliance notes
    into a multi-sheet Excel workbook. It also includes example Copilot prompts.

    Args:
        df (pd.DataFrame): The pandas DataFrame containing the logistics manifest data.
        summary_text (str): A string containing the AI-generated summary of the manifest.
        compliance_notes (list, optional): A list of strings, each representing a compliance issue.
                                          If None or empty, the "Compliance" sheet is not created.

    Returns:
        str: The full path to the generated Excel file.
    """
    wb = Workbook() # Create a new Excel workbook.
    ws1 = wb.active # Get the active (first) worksheet.
    ws1.title = "Manifest" # Set the title of the first worksheet to "Manifest".

    # Write manifest data from the pandas DataFrame to the first worksheet.
    # index=False prevents writing the DataFrame index as a column.
    # header=True ensures the DataFrame column names are written as the first row.
    for r in dataframe_to_rows(df, index=False, header=True):
        ws1.append(r) # Append each row from the DataFrame to the worksheet.

    # Add example formulas for potential "Copilot" (or Excel's AI features) integration.
    # These formulas are written directly into specific cells.
    ws1["F1"] = "Delay Risk" # Header for the "Delay Risk" column.
    # Formula to check if today's date minus the date in column D (DepartureDate) is greater than 5 days.
    # If true, it shows "⚠️ Delay Risk", otherwise an empty string. This assumes D2 is the first data row's date.
    ws1["F2"] = "=IF(TODAY()-D2>5, \"⚠️ Delay Risk\", \"\")"
    ws1["G1"] = "Delivered?" # Header for the "Delivered?" column.
    # Formula to check if the status in column C (Status) is "Delivered".
    # If true, it shows "✅", otherwise an empty string. This assumes C2 is the first data row's status.
    ws1["G2"] = "=IF(C2=\"Delivered\", \"✅\", \"\")"

    # Create a new sheet for the AI Summary.
    ws2 = wb.create_sheet("AI Summary")
    ws2.append(["Generated Summary"]) # Add a header for the summary.
    # Split the summary text by newlines and add each line as a separate row.
    for line in summary_text.split("\n"):
        ws2.append([line])

    # Add a Compliance Notes sheet if compliance_notes are provided.
    if compliance_notes:
        ws3 = wb.create_sheet("Compliance") # Create the "Compliance" worksheet.
        ws3.append(["Compliance Issues"]) # Add a header for compliance issues.
        for note in compliance_notes: # Iterate through each compliance note.
            ws3.append([note]) # Add each note as a separate row.

    # Define example prompts for an Excel Copilot feature.
    prompts = [
        ["Prompt Example", "Description"], # Header row for the prompts table.
        ["Highlight all delayed shipments", "Uses conditional formatting to tag 'Delayed' rows"],
        ["Summarise carrier performance", "Group by Carrier and count statuses"],
        ["Group by destination and count delays", "Build pivot table using Status column"],
        ["Add delay risk indicator", "Use formula: =IF(TODAY()-[@ShipDate]>5, '⚠️ Delay Risk', '')"],
        ["Mark delivered shipments", "Use formula: =IF([@Status]='Delivered', '✅', '')"]
    ]
    ws4 = wb.create_sheet("Copilot Prompts") # Create a new sheet for Copilot prompts.
    for row in prompts: # Iterate through the list of prompts.
        ws4.append(row) # Append each prompt example row to the worksheet.
    ws4["A1"].font = ws4["B1"].font = Font(bold=True) # Make the header row (A1 and B1) bold.

    # Generate a unique filename using a timestamp to avoid overwrites.
    # The file is saved in the /tmp directory, which is common for temporary files.
    filename = f"/tmp/export_logibot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename) # Save the entire workbook to the generated filename.
    return filename # Return the path to the saved Excel file.