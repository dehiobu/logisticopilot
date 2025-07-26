import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime

def export_manifest_to_excel(df, summary_text, compliance_notes=None):
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Manifest"
    for r in dataframe_to_rows(df, index=False, header=True):
        ws1.append(r)

    ws2 = wb.create_sheet("AI Summary")
    ws2.append(["Generated Summary"])
    for line in summary_text.split("\n"):
        ws2.append([line])

    if compliance_notes:
        ws3 = wb.create_sheet("Compliance")
        ws3.append(["Compliance Issues"])
        for note in compliance_notes:
            ws3.append([note])

    filename = f"/tmp/export_logibot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    return filename
