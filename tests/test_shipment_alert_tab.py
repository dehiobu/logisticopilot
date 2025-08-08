```python
import unittest # Imports the unittest module for creating and running tests.
from unittest.mock import patch # Imports 'patch' from unittest.mock, used for mocking objects during tests.
from tabs.shipment_alert_tab import ( # Imports specific functions from the 'shipment_alert_tab' module.
    load_delayed_shipments_from_csv, # Function to load delayed shipments from a CSV.
    format_multi_shipment_alert, # Function to format an alert message for multiple delayed shipments.
    rewrite_tone # Function to rewrite the tone of a message using an LLM.
)

# Sample data representing delayed shipments. This list of dictionaries
# serves as a predefined input for testing purposes.
sample_shipments = [
    {
        "shipment_id": "SH001",
        "status": "Delayed due to weather",
        "eta": "2025-07-30",
        "action": "Carrier rerouting"
    },
    {
        "shipment_id": "SH002",
        "status": "Delayed at customs",
        "eta": "2025-08-01",
        "action": "Clearance pending"
    }
]

# Defines a test class that inherits from unittest.TestCase.
# Each method starting with 'test_' will be executed as a separate test case.
class TestShipmentAlertTab(unittest.TestCase):

    def test_format_multi_shipment_alert(self):
        """
        Test the natural language generation of delay messages.
        This test verifies that the 'format_multi_shipment_alert' function
        correctly renders the template with the provided sample data,
        checking for key phrases and shipment IDs in the output.
        """
        result = format_multi_shipment_alert(sample_shipments) # Calls the function to be tested with sample data.
        self.assertIn("2 shipments", result) # Asserts that the string "2 shipments" is present in the result.
        self.assertIn("SH001", result) # Asserts that "SH001" (a shipment ID) is in the result.
        self.assertIn("SH002", result) # Asserts that "SH002" (another shipment ID) is in the result.

    @patch("tabs.shipment_alert_tab.OpenAI") # Uses the @patch decorator to mock the 'OpenAI' class within the 'shipment_alert_tab' module.
    def test_rewrite_tone(self, mock_openai):
        """
        Test tone rewriting with OpenAI mocked.
        This test ensures that the 'rewrite_tone' function correctly interacts
        with the mocked OpenAI API and returns the expected rewritten message.
        Mocking prevents actual API calls during testing.
        """
        mock_instance = mock_openai.return_value # Gets the mock instance that 'OpenAI()' would return.
        mock_instance.invoke.return_value = "Friendly message here." # Configures the mock instance's 'invoke' method to return a predefined string.

        result = rewrite_tone("Original message.", tone="friendly") # Calls the function to be tested with a dummy message and tone.
        self.assertEqual(result, "Friendly message here.") # Asserts that the function's result matches the mocked return value.

    def test_load_delayed_shipments_from_csv(self):
        """
        Test that the loader extracts only delayed rows from a test CSV.
        This test creates a temporary CSV file, populates it with mixed data
        (some delayed, some not), and then verifies that 'load_delayed_shipments_from_csv'
        correctly filters and returns only the delayed shipments.
        """
        import tempfile # Imports the tempfile module for creating temporary files.
        import csv # Imports the csv module for reading/writing CSV files.

        # Create a temporary CSV file with mixed statuses
        # 'NamedTemporaryFile' creates a temporary file that can be accessed by name.
        # 'mode='w+'' allows reading and writing. 'delete=False' keeps the file after 'with' block for inspection if needed.
        # 'newline=''' is important for CSV writing to prevent extra blank rows.
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, newline='', suffix=".csv") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=["shipment_id", "status", "eta", "action"]) # Creates a CSV writer.
            writer.writeheader() # Writes the header row to the CSV.
            writer.writerow({"shipment_id": "S1", "status": "In Transit", "eta": "2025-07-30", "action": ""}) # Writes a non-delayed row.
            writer.writerow({"shipment_id": "S2", "status": "Delayed due to rain", "eta": "2025-07-31", "action": "Hold"}) # Writes a delayed row.
            writer.writerow({"shipment_id": "S3", "status": "Delayed at customs", "eta": "2025-08-01", "action": "Inspect"}) # Writes another delayed row.

            tmp.flush() # Ensures all buffered data is written to the file system.

            # Call the loader with this temp file
            result = load_delayed_shipments_from_csv(tmp.name) # Calls the function to be tested, passing the path to the temporary CSV.

        # Assertions to verify the correctness of the loaded data.
        self.assertEqual(len(result), 2) # Asserts that exactly 2 delayed shipments were found.
        self.assertEqual(result[0]["shipment_id"], "S2") # Asserts the ID of the first delayed shipment.
        self.assertEqual(result[1]["shipment_id"], "S3") # Asserts the ID of the second delayed shipment.


if __name__ == "__main__":
    unittest.main() # Runs all tests defined in the TestShipmentAlertTab class when the script is executed directly.

```