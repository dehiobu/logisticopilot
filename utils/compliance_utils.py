import pandas as pd
from utils.carrier_utils import load_approved_carriers

def check_manifest_compliance(df: pd.DataFrame, approved_carriers: list) -> list:
    """
    Check the uploaded manifest DataFrame for compliance issues.

    Args:
        df (pd.DataFrame): Uploaded manifest data
        approved_carriers (list): List of approved carrier names

    Returns:
        list: Human-readable list of compliance issues found
    """
    issues = []

    # Normalise column headers
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "")

    # Check for missing tracking IDs
    if "trackingnumber" in df.columns:
        missing_tracking = df[df["trackingnumber"].isnull()]
        for idx, row in missing_tracking.iterrows():
            issues.append(f"❌ Shipment {row.get('shipmentid', 'UNKNOWN')} missing tracking number.")

    # Check for unapproved carriers
    if "carrier" in df.columns:
        for idx, row in df.iterrows():
            carrier = str(row.get("carrier", "")).strip().lower()
            if carrier and carrier not in approved_carriers:
                issues.append(f"⚠️ Carrier '{carrier}' in shipment {row.get('shipmentid', 'UNKNOWN')} not approved.")

    if not issues:
        issues.append("✅ No compliance issues found.")

    return issues
