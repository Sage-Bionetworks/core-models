import json
import requests

# Fetch the JSON-LD data from the URL
url = "https://raw.githubusercontent.com/nf-osi/nf-metadata-dictionary/refs/heads/main/NF.jsonld"
response = requests.get(url)

if response.status_code == 200:
    # Load the JSON-LD data
    data = response.json()

    # Find the Platform entry in the @graph
    platform_entry = next((item for item in data['@graph'] if item['@id'] == 'bts:Platform'), None)

    if platform_entry:
        # Extract the enum values from "schema:rangeIncludes" and remove 'bts:' prefix
        platforms = [item['@id'].replace('bts:', '') for item in platform_entry['schema:rangeIncludes']]

        # Create a JSON schema
        form_schema = {
            "title": "Submit Cell Line",
            "type": "object",
            "properties": {
                "cellLineName": {
                    "type": "string",
                    "title": "Cell Line Name"
                },
                "platform": {
                    "type": "string",
                    "title": "Platform",
                    "enum": platforms  # Insert fetched platform values without 'bts:' prefix
                }
            },
            "required": ["cellLineName", "platform"]
        }

        # Write the schema to a JSON file
        with open("cell_line_form_schema_no_bts.json", "w") as f:
            json.dump(form_schema, f, indent=2)

        print("Form schema generated and saved as 'cell_line_form_schema_no_bts.json'")
    else:
        print("Platform entry not found in the JSON-LD data.")
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")
