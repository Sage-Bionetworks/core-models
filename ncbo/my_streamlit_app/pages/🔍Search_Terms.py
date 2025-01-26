import streamlit as st
import urllib.parse
import requests
import json
from config import API_KEY

st.set_page_config(page_title="Chatbot Search Tool", page_icon="💬")

REST_URL = "http://data.bioontology.org"

# Initialize session state variables
if 'selected_terms' not in st.session_state:
    st.session_state.selected_terms = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'checkbox_states' not in st.session_state:
    st.session_state.checkbox_states = {}

def handle_checkbox_change(key, id_, pref_label):
    """Handle checkbox state changes"""
    if st.session_state[key]:  # If checkbox is checked
        term = {"id": id_, "label": pref_label}
        if term not in st.session_state.selected_terms:
            st.session_state.selected_terms.append(term)
    else:  # If checkbox is unchecked
        st.session_state.selected_terms = [
            term for term in st.session_state.selected_terms if term["id"] != id_
        ]

def get_json_sync(url):
    headers = {'Authorization': f'apikey token={API_KEY}'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: Unable to fetch data (status code: {response.status_code})")
            return None
    except requests.RequestException as e:
        st.error(f"Network error occurred: {e}")
        return None

def display_annotations():
    if st.session_state.selected_terms:
        # Render the export button at the top
        export_button()

    for idx, result in enumerate(st.session_state.search_results):
        id_ = result.get("@id", "N/A")
        pref_label = result.get("prefLabel", "N/A")
        definitions = result.get("definition", ["N/A"])
        definition = definitions[0] if definitions else "N/A"

        st.write(f"**ID**: {id_}")
        st.write(f"**Preferred Label**: {pref_label}")
        st.write(f"**Definition**: {definition}")

        # Create a unique key for the checkbox
        checkbox_key = f"checkbox_{idx}"

        # Initialize the checkbox state if it doesn't exist
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False

        # Create the checkbox with a callback
        st.checkbox(
            f"Select '{pref_label}'",
            key=checkbox_key,
            value=st.session_state[checkbox_key],
            on_change=handle_checkbox_change,
            args=(checkbox_key, id_, pref_label)
        )
        st.write("---")

def export_button():
    """Render the export button."""
    # Generate JSON-LD content
    jsonld_content = {
        "@context": "https://schema.org/",
        "@graph": [
            {"@id": term["id"], "label": term["label"]} for term in st.session_state.selected_terms
        ]
    }
    jsonld_str = json.dumps(jsonld_content, indent=2)

    # Get the count of selected terms
    selected_count = len(st.session_state.selected_terms)

    # Render the download button at the top
    st.download_button(
        label=f"Export {selected_count} Selected Terms as JSON-LD",
        data=jsonld_str,
        file_name="selected_terms.jsonld",
        mime="application/ld+json",
        on_click=reset_checkboxes,
    )

def reset_checkboxes():
    """Reset all checkboxes and clear selected terms after export."""
    for key in list(st.session_state.keys()):
        if key.startswith("checkbox_"):
            st.session_state[key] = False
    st.session_state.selected_terms = []

def main():
    st.title("💬 Chatbot Search Tool")
    st.write("Hello! I'm here to help you search for medical terms. How can I assist you today?")

    search_term = st.text_input("You: ")

    if st.button("Search", key="send_search"):
        if search_term:
            st.write(f"Chatbot: Let me check for information about '{search_term}'...")
            encoded_term = urllib.parse.quote(search_term)
            url = f"{REST_URL}/search?q={encoded_term}"
            try:
                annotations = get_json_sync(url)
                if annotations and "collection" in annotations and len(annotations["collection"]) > 0:
                    st.session_state.search_results = annotations["collection"][:20]
                else:
                    st.warning("No matching results found.")
            except Exception as e:
                st.error(f"An error occurred while processing your request: {e}")

    # Display search results and checkboxes
    if st.session_state.search_results:
        display_annotations()

if __name__ == "__main__":
    main()
