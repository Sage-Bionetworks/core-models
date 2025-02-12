import json

def transform_jsonld_to_react_form(jsonld_data):
    question_id = jsonld_data["@id"]
    react_form = {
        "title": "",
        "type": "object",
        "properties": {
            f"{question_id}Module": {
                "type": "object",
                "title": "",
                "properties": {
                    f"@id:{question_id}": {
                        "type": "string",
                        "title": f"{jsonld_data['displayName']}",

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

#A1
with open("modules/a1.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a1_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a1_form.json.")

#A2
with open("modules/a2.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a2_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a2_form.json.")

#A3
with open("modules/a3.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a3_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a3_form.json.")

#A4
with open("modules/a4.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a4_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a4_form.json.")

#A5
with open("modules/a5.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a5_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a5_form.json.")

#A6
with open("modules/a6.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a6_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a6_form.json.")

#A7
with open("modules/a7.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a7_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a7_form.json.")

#A8
with open("modules/a8.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a8_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a8_form.json.")

#A9
with open("modules/a9.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a9_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a9_form.json.")


#A10
with open("modules/a10.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a10_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a10_form.json.")

#A11
with open("modules/a11.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a11_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a11_form.json.")

#A12
with open("modules/a12.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a12_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a12_form.json.")

#A13
with open("modules/a13.json", "r") as f:
    jsonld_data = json.load(f)
react_form_data = transform_jsonld_to_react_form(jsonld_data)
with open("a13_form.json", "w") as f:
    json.dump(react_form_data, f, indent=2)
print("Transformation complete. Output saved as a13_form.json.")