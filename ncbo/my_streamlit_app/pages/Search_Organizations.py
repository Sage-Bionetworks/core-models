import streamlit as st
import requests
import json

st.set_page_config(page_title="Search Organizations", page_icon="🔍")

ROR_API_URL = "https://api.ror.org/organizations"

# Initialize session state variables
if 'bucket' not in st.session_state:
    st.session_state.bucket = []  # Stores all selected organizations
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'checkbox_states' not in st.session_state:
    st.session_state.checkbox_states = {}  # Stores checkbox states for current results

def handle_checkbox_change(key, id_, name):
    """Handle checkbox state changes."""
    if st.session_state[key]:  # If checkbox is checked
        organization = {"id": id_, "name": name}
        if organization not in st.session_state.bucket:
            st.session_state.bucket.append(organization)
    else:  # If checkbox is unchecked
        st.session_state.bucket = [
            org for org in st.session_state.bucket if org["id"] != id_
        ]

def get_organizations(query):
    """Fetch organizations from ROR API."""
    try:
        response = requests.get(f"{ROR_API_URL}?query={query}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: Unable to fetch data (status code: {response.status_code})")
            return None
    except requests.RequestException as e:
        st.error(f"Network error occurred: {e}")
        return None

def display_organizations():
    """Display search results."""
    for idx, org in enumerate(st.session_state.search_results):
        id_ = org.get("id", "N/A")
        name = org.get("name", "N/A")
        acronyms = ", ".join(org.get("acronyms", [])) or "None"
        types = ", ".join(org.get("types", [])) or "None"
        city = org["addresses"][0].get("city", "Unknown") if org.get("addresses") else "Unknown"
        country = org.get("country", {}).get("country_name", "Unknown")

        st.write(f"**Name**: {name}")
        st.write(f"**ID**: {id_}")
        st.write(f"**Acronyms**: {acronyms}")
        st.write(f"**Types**: {types}")
        st.write(f"**Location**: {city}, {country}")

        # Create a unique key for the checkbox
        checkbox_key = f"checkbox_{idx}"

        # Initialize the checkbox state if it doesn't exist
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False

        # Create the checkbox with a callback
        st.checkbox(
            f"Add '{name}' to bucket",
            key=checkbox_key,
            value=st.session_state[checkbox_key],
            on_change=handle_checkbox_change,
            args=(checkbox_key, id_, name)
        )
        st.write("---")

def export_bucket():
    """Export the entire bucket as JSON-LD."""
    jsonld_content = {
        "@context": "https://schema.org/",
        "@graph": [
            {"@id": org["id"], "name": org["name"]} for org in st.session_state.bucket
        ]
    }
    jsonld_str = json.dumps(jsonld_content, indent=2)
    selected_count = len(st.session_state.bucket)

    st.download_button(
        label=f"Export {selected_count} Organizations as JSON-LD",
        data=jsonld_str,
        file_name="organizations_bucket.jsonld",
        mime="application/ld+json",
    )

def main():
    st.title("🔍 Research Organization Search Tool")
    st.write("Search for organizations from the Research Organization Registry (ROR) and add them to a bucket.")

    # Display the selected organizations bucket at the top
    if st.session_state.bucket:
        with st.container():
            st.markdown(
                """
                <div style="padding: 15px; background-color: #f0f8ff; border: 1px solid #000; border-radius: 5px;">
                    <h3 style="color: #333;">Selected Organizations</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            for org in st.session_state.bucket:
                st.write(f"- **{org['name']}** ({org['id']})")
            export_bucket()

    search_query = st.text_input("Enter an organization name or keyword:")

    if st.button("Search"):
        if search_query:
            # Clear previous checkbox states
            st.session_state.checkbox_states = {}
            st.write(f"Searching for organizations matching '{search_query}'...")
            results = get_organizations(search_query)
            if results and "items" in results:
                st.session_state.search_results = results["items"][:20]
            else:
                st.warning("No matching results found.")

    if st.session_state.search_results:
        display_organizations()

if __name__ == "__main__":
    main()
