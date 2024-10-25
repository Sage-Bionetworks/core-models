import json

def import_and_replace_ids(input_file, output_file):
    # Load the form and the context mapping from a file
    with open(input_file, 'r') as file:
        data = json.load(file)
        form = data["form"]
        context_mapping = data["context_mapping"]

    # Create a mapping from @id to displayName
    id_to_display_name = {item["@id"]: item["displayName"] for item in context_mapping["@graph"]}

    # Function to replace @ids in the form with display names
    def replace_ids_with_display_names(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.startswith("@id:"):
                    id_value = value.split(":", 1)[1]
                    if id_value in id_to_display_name:
                        data[key] = id_to_display_name[id_value]
                else:
                    replace_ids_with_display_names(value)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, str) and item.startswith("@id:"):
                    id_value = item.split(":", 1)[1]
                    if id_value in id_to_display_name:
                        data[index] = id_to_display_name[id_value]
                else:
                    replace_ids_with_display_names(item)

    # Replace @ids with display names in the form
    replace_ids_with_display_names(form)

    # Write the updated form to the output file
    with open(output_file, 'w') as file:
        json.dump(form, file, indent=2)

# Example usage
