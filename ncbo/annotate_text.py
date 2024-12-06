import asyncio
import aiohttp
import urllib.parse
import json
from config import API_KEY

REST_URL = "http://data.bioontology.org"

# Asynchronous function to get JSON data
async def get_json_async(url, session):
    headers = {'Authorization': 'apikey token=' + API_KEY}
    async with session.get(url, headers=headers) as response:
        return await response.json()

# Function to display annotations in the chat
async def display_annotations(annotations, session, get_class=True):
    tasks = []
    for result in annotations[:5]:  # Limiting to 5 annotations
        class_details = result["annotatedClass"]
        if get_class:
            tasks.append(asyncio.ensure_future(get_json_async(result["annotatedClass"]["links"]["self"], session)))
        else:
            tasks.append(class_details)

    # Gather results for async tasks
    if get_class:
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    else:
        responses = tasks

    # Display the responses in the chat
    for class_details in responses:
        if isinstance(class_details, dict):
            id_ = class_details.get("@id", "N/A")
            pref_label = class_details.get("prefLabel", "N/A")
            ontology = class_details.get("links", {}).get("ontology", "N/A")
            print(f"ID: {id_}\nPreferred Label: {pref_label}\nOntology: {ontology}\n")

# Main function to handle annotation retrieval
async def main():
    text_to_annotate = "Melanoma is a malignant tumor of melanocytes which are found predominantly in skin but also in the bowel and the eye."

    # Create a session for HTTP requests
    async with aiohttp.ClientSession() as session:
        # Annotate using the provided text
        annotations = await get_json_async(REST_URL + "/annotator?text=" + urllib.parse.quote(text_to_annotate), session)
        await display_annotations(annotations, session)

        # Annotate with hierarchy information
        annotations = await get_json_async(REST_URL + "/annotator?max_level=3&text=" + urllib.parse.quote(text_to_annotate), session)
        await display_annotations(annotations, session)

        # Annotate with prefLabel, synonym, definition returned
        annotations = await get_json_async(REST_URL + "/annotator?include=prefLabel,synonym,definition&text=" + urllib.parse.quote(text_to_annotate), session)
        await display_annotations(annotations, session, get_class=False)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
