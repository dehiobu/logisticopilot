from langchain.prompts import PromptTemplate # Importing PromptTemplate, likely for defining structured prompts for LLMs (though not directly used in the provided snippet's core logic).
from jinja2 import Template # Importing Template from Jinja2, a popular templating engine for Python, used here to render dynamic text.

# Template used to summarise one or more delayed shipments in a natural language block.
# This multi-line string defines a Jinja2 template. It includes placeholders (e.g., {{ variable }})
# and control structures (e.g., {% for ... %}, {% if ... %}) that will be filled/processed
# with actual data when the template is rendered.
multi_prompt_template = """
🤖 **LogiBot's Answer**

{{ delay_count }} shipment{{ 's' if delay_count > 1 else '' }} currently delayed:
{# The line above dynamically adds an 's' to "shipment" if delay_count is greater than 1, for correct grammar. #}

{% for s in shipments %} {# Loops through each shipment dictionary in the 'shipments' list. #}
- **Shipment ID:** {{ s.shipment_id }} {# Accesses the 'shipment_id' key from the current shipment dictionary. #}
  • **Status:** {{ s.status }} {# Accesses the 'status' key. #}
  • **ETA:** {{ s.eta }} {# Accesses the 'eta' (Estimated Time of Arrival) key. #}
  • **Action:** {{ s.action }} {# Accesses the 'action' key, suggesting a recommended action for the delayed shipment. #}
{% endfor %} {# Ends the for loop. #}
"""

def format_multi_shipment_alert(shipments: list) -> str:
    """
    Renders a delay summary using the Jinja2 template and provided shipment data.

    Args:
        shipments (list): A list of dictionaries, where each dictionary represents a
            single delayed shipment. Each dictionary is expected to have the following keys:
            - shipment_id (str): Unique identifier for the shipment.
            - status (str): Current status of the shipment (e.g., "Delayed", "In Transit").
            - eta (str): Estimated time of arrival or delay information.
            - action (str): Recommended action to take for this specific shipment.

    Returns:
        str: The rendered alert message, formatted as a natural language block,
            ready for display or further processing by LogiBot.
    """
    # Create a Jinja2 Template object from the multi_prompt_template string.
    template = Template(multi_prompt_template)

    # Count the number of delayed shipments for dynamic text.
    delay_count = len(shipments)

    # Render the template with the provided data.
    # The 'render' method fills the placeholders in the template with actual values.
    return template.render(shipments=shipments, delay_count=delay_count)
