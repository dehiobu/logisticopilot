import os
import json

CARRIER_FILE = open("data/approved_carriers.json", "r")

def load_approved_carriers():
    if os.path.exists(CARRIER_FILE):
        with open(CARRIER_FILE, "r") as f:
            return json.load(f)
    return []

def save_approved_carriers(carriers):
    with open(CARRIER_FILE, "w") as f:
        json.dump(carriers, f)