import os
import json

# Define the file path for storing approved carriers.
# This path is relative to the script's execution directory.
CARRIER_FILE = "data/approved_carriers.json"

def load_approved_carriers():
    """
    Loads and returns the list of approved carriers from the JSON file.
    If the file does not exist, it gracefully returns an empty list,
    preventing a FileNotFoundError.
    """
    # Check if the carrier file exists at the specified path.
    if os.path.exists(CARRIER_FILE):
        try:
            # Open the file in read mode ('r').
            with open(CARRIER_FILE, "r") as f:
                # Load the JSON content from the file and return it as a Python list.
                return json.load(f)
        except json.JSONDecodeError:
            # Handle cases where the file exists but contains invalid JSON.
            # This prevents errors if the file is empty or corrupted.
            print(f"Warning: {CARRIER_FILE} contains invalid JSON. Returning empty list.")
            return []
    # If the file does not exist, return an empty list.
    return []

def save_approved_carriers(carriers: list):
    """
    Overwrites (or creates) the JSON file with the updated list of carriers.
    Ensures that the parent directory ('data/') exists before attempting to write the file.

    Args:
        carriers (list): A list of strings, where each string is an approved carrier name.
    """
    # Extract the directory path from the CARRIER_FILE path.
    data_directory = os.path.dirname(CARRIER_FILE)
    
    # Create the directory if it does not already exist.
    # 'exist_ok=True' prevents an error if the directory already exists.
    if data_directory: # Only try to create if data_directory is not an empty string (i.e., not current directory)
        os.makedirs(data_directory, exist_ok=True)

    # Open the file in write mode ('w'). If the file doesn't exist, it will be created.
    # If it exists, its content will be overwritten.
    with open(CARRIER_FILE, "w") as f:
        # Dump the 'carriers' list into the JSON file.
        # 'indent=4' makes the JSON output human-readable with 4-space indentation.
        json.dump(carriers, f, indent=4)