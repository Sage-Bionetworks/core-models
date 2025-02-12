import json

def transform_jsonld_to_react_form(jsonld_data):
    question_id = jsonld_data["@id"]
    react_form = {
        "title": "Section 1",
        "type": "object",
        "properties": {
            f"{question_id}Module": {
                "type": "object",
                "title": "",
                "properties": {
                    f"@id:{question_id}": {
                        "type": "string",
                        "title": f"Will you require {jsonld_data['displayName']}?",

                        "enum": [], "default": next((d['displayName'] for d in jsonld_data.get('requiresDependency', []) if d['@id'].endswith('e1')), 'No data processing is required.')
                    }
                }
            }
        },
        "allOf": []
    }

    for dependency in sorted(jsonld_data.get("requiresDependency", []), key=lambda d: d["@id"]):
        display_name = dependency["displayName"]
        react_form["properties"][f"{question_id}Module"]["properties"][f"@id:{question_id}"]["enum"].append(display_name)

        if "element" in dependency:
            job_roles_dict = {}
            job_roles = []
            for role in dependency["element"]:
                job_roles_dict[f"{role.get('displayName', 'Unknown Role')}"] = {"type": "string", "title": f"{role.get('displayName', 'Unknown Role')}", "default": f"{role.get('sizeFirstYear', '?')}"}

            then_schema = {
                "properties": {
                    f"{question_id}Module": {
                        "properties": {
                            "rModule": {"title": "",
                                "title": "",
                                "type": "object", "properties": {"description": "","title":"Recommended Roles", "jobRoles": {"title": "Recommended Roles", "type": "object", "properties": job_roles_dict}}
                            }
                        }
                    }
                }
            }

            react_form["allOf"].append({
                "if": {
                    "properties": {
                        f"{question_id}Module": {
                            "properties": {
                                f"@id:{question_id}": {"enum": [display_name]}
                            }
                        }
                    }
                },
                "then": then_schema
            })

    return react_form

# Load JSON-LD data
with open("data.jsonld", "r") as f:
    jsonld_data = json.load(f)

# Transform JSON-LD to React JSON form
react_form_data = transform_jsonld_to_react_form(jsonld_data)

# Save transformed JSON
with open("react_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)

print("Transformation complete. Output saved as react_form.json.")
