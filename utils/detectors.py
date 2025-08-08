import csv

def load_delayed_shipments_from_csv(path="data/shipments.csv"):
    """
    Reads a CSV file and filters out rows where the shipment is delayed.

    Args:
        path (str): Path to the shipment CSV file.

    Returns:
        list: A list of dictionaries representing delayed shipments.
    """
    delayed = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'].lower().startswith('delayed'):
                delayed.append({
                    "shipment_id": row["shipment_id"],
                    "status": row["status"],
                    "eta": row["eta"],
                    "action": row["action"]
                })
    return delayed
