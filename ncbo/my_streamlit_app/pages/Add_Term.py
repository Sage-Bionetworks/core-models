import streamlit as st
import requests
import json
from config import CORE_MODELS_API_KEY

# Streamlit app configuration
st.set_page_config(page_title="Add Node to Core Models", page_icon="🧩")

# API base URL
API_BASE_URL = "https://go.coremodels.io"

# Main function to render the app
def main():
    st.title("Add a New Node to Core Models")
    st.write("Use this page to create a new node in Core Models.")

    # Input field for Project ID
    project_id = st.text_input("Project ID", help="Enter the Project ID for Core Models.")

    # Input fields for node creation
    label = st.text_input("Node Label", help="The label for the node.")
    node_type = st.selectbox(
        "Node Type",
        options=["Element", "Type", "Taxonomy", "Exemplar", "Component", "Space", "Tag", "Mixin"],
        help="Select the type of the node."
    )
    space_ids = st.text_input(
        "Space IDs (comma-separated)",
        help="Comma-separated list of space IDs where this node will be created."
    )
    check_before_create = st.checkbox(
        "Check Before Create",
        value=False,
        help="Check if the label is already in use before creating the node."
    )

    # Submit button
    if st.button("Create Node"):
        # Ensure Project ID is provided
        if not project_id:
            st.error("Project ID is required to create a node.")
            return

        # Convert space IDs to a list
        space_ids_list = [space_id.strip() for space_id in space_ids.split(",") if space_id.strip()]

        # Prepare the payload
        payload = {
            "label": label,
            "nodeType": node_type,
            "checkBeforeCreate": check_before_create,
            "spaceIds": space_ids_list
        }

        # Headers
        headers = {
            "Content-Type": "application/json-patch+json",
            "Authorization": f"Bearer {CORE_MODELS_API_KEY}"
        }

        # API endpoint
        url = f"{API_BASE_URL}/v1/{project_id}/node"

        # Make the API call
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("success"):
                st.success(f"Node created successfully! Node ID: {response_data['data']['id']}")
            else:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                st.error(f"Failed to create node. Error: {error_message}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
