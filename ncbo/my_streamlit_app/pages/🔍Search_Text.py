import aiohttp
import urllib.parse
import streamlit as st
import asyncio
import nest_asyncio
from config import API_KEY

# Patching the existing event loop to avoid "RuntimeError: There is no current event loop"
nest_asyncio.apply()

st.set_page_config(page_title="Large Text Search", page_icon="📝")

REST_URL = "http://data.bioontology.org"

# Asynchronous function to get JSON data
async def get_json_async(url, session):
    headers = {'Authorization': 'apikey token=' + API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            st.error(f"Error fetching data: Status code {response.status}")
            return None

# Function to display annotations in the Streamlit app
def display_annotations(annotations):
    for result in annotations[:100]:  # Limiting to 100 annotations
        annotated_class = result.get("annotatedClass", {})

        # Extract relevant fields
        id_ = annotated_class.get("@id", "N/A")

        # Use the "text" from the "annotations" list instead of "prefLabel"
        annotation_text = result.get("annotations", [])
        if annotation_text and isinstance(annotation_text, list):
            pref_label = annotation_text[0].get("text", "N/A")
        else:
            pref_label = "N/A"

        # Display the annotation details in Streamlit
        st.write(f"**ID**: {id_}")
        st.write(f"**Preferred Label**: {pref_label}")
        st.write("---")

# Main function for annotation retrieval
async def main(session, text_to_annotate):
    # Annotate using the provided text
    url = f"{REST_URL}/annotator?text={urllib.parse.quote(text_to_annotate)}"
    annotations = await get_json_async(url, session)

    if annotations and isinstance(annotations, list) and len(annotations) > 0:
        display_annotations(annotations)
    else:
        st.warning("No annotations found in the response.")

# Streamlit UI
st.title("Large-Text Annotation Tool")
text_to_annotate = st.text_area("Enter text to annotate:", "Melanoma is a malignant tumor of melanocytes...")

if st.button("Annotate Text"):
    with st.spinner("Fetching annotations..."):
        async def run():
            async with aiohttp.ClientSession() as session:
                await main(session, text_to_annotate)

        # Run the async function with asyncio.run()
        asyncio.run(run())
