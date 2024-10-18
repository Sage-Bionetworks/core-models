import json
import requests

def fetch_jsonld_data(url):
    """Fetch the JSON-LD data from the given URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data from {url}. Status code: {response.status_code}")

def extract_enum_values(data, jsonld_id):
    """Extract the enum values from the JSON-LD data given an @id."""
    entry = next((item for item in data['@graph'] if item['@id'] == jsonld_id), None)
    if entry and 'schema:rangeIncludes' in entry:
        return [item['@id'].replace('bts:', '') for item in entry['schema:rangeIncludes']]
    else:
        raise Exception(f"No entry found for {jsonld_id} or 'schema:rangeIncludes' is missing.")

def update_form_schema(schema, field_name, enum_values):
    """Update the form schema with the extracted enum values for the specified field."""
    if "properties" in schema:
        if field_name in schema["properties"]["addModule"]["properties"]["module"]["items"]["properties"]:
            schema["properties"]["addModule"]["properties"]["module"]["items"]["properties"][field_name]["enum"] = enum_values
        else:
            raise Exception(f"Field '{field_name}' not found in the form schema.")
    else:
        raise Exception("Form schema does not have 'properties'.")

def main():
    # Load the initial form schema from a JSON file
    with open("allocationForm.json", "r") as f:
        form_schema = json.load(f)

    # URL to fetch the JSON-LD data
    jsonld_url = "https://raw.githubusercontent.com/Sage-Bionetworks/core-models/refs/heads/main/draft-data-models/sage-allocation/allocation.jsonld"
    data = fetch_jsonld_data(jsonld_url)

    # Field and JSON-LD @id to update
    field_to_update = {
        "productService": "bts:ProductService"
    }

    # Iterate over the fields and update the schema
    for field, jsonld_id in field_to_update.items():
        try:
            enum_values = extract_enum_values(data, jsonld_id)
            update_form_schema(form_schema, field, enum_values)
            print(f"Updated '{field}' with values from '{jsonld_id}'")
        except Exception as e:
            print(f"Failed to update '{field}': {e}")

    # Write the updated schema to a new JSON file
    with open("updated_formSchema.json", "w") as f:
        json.dump(form_schema, f, indent=2)

    print("Form schema updated and saved as 'updated_formSchema.json'")

if __name__ == "__main__":
    main()
