import asyncio
import aiohttp
import urllib.parse
from config import API_KEY

REST_URL = "http://data.bioontology.org"

# Asynchronous function to get JSON data
async def get_json_async(url, session):
    headers = {'Authorization': 'apikey token=' + API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Error: Unable to fetch data from {url} (status code: {response.status})")
            return None

# Function to display annotations in a user-friendly way
async def display_annotations(annotations):
    if not annotations or "collection" not in annotations:
        print("No annotations found or invalid response.")
        return

    # Limit to 20 annotations that match the ID conditions
    filtered_results = [
        result for result in annotations["collection"]
        if result.get("@id", "").startswith(("http://purl.bioontology.org/ontology",
                                             "http://purl.obolibrary.org/obo/",
                                             "http://www.ebi.ac.uk/"))
    ][:20]

    if not filtered_results:
        print("No matching results found based on the ID criteria.")
        return

    for result in filtered_results:
        # Extract relevant fields from the result
        id_ = result.get("@id", "N/A")
        pref_label = result.get("prefLabel", "N/A")

        # Check if "definition" key exists and if it contains values
        definitions = result.get("definition", [])
        if isinstance(definitions, list) and len(definitions) > 0:
            definition = definitions[0]
        else:
            definition = "N/A"

        # Display the annotation details
        print(f"ID: {id_}\nPreferred Label: {pref_label}\nDefinition: {definition}\n")

# Main function to handle user input and annotation retrieval
async def main():
    print("Welcome to the Interactive Class Search Tool!")

    async with aiohttp.ClientSession() as session:
        while True:
            search_term = input("\nEnter a term to search (or type 'exit' to quit): ").strip()
            if search_term.lower() == 'exit':
                print("Goodbye!")
                break

            # Encode the user's input for the URL
            encoded_term = urllib.parse.quote(search_term)
            url = f"{REST_URL}/search?q={encoded_term}"

            # Fetch the search results from the API
            annotations = await get_json_async(url, session)

            # Display the results
            if annotations and "collection" in annotations and len(annotations["collection"]) > 0:
                print(f"\nResults for '{search_term}':")
                await display_annotations(annotations)
            else:
                print(f"No results found for '{search_term}'. Try a different term.")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
