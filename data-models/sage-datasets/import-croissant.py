import json
import requests
import argparse
import yaml

# Load Synapse API parameters from config.yaml
with open("syn_auth_token.yml", "r") as file:
    config = yaml.safe_load(file)

BASE_URL = "https://repo-prod.prod.sagebase.org/repo/v1"
SYNAPSE_AUTH_TOKEN = config["synapse"]["auth_token"]

# Headers for authentication
HEADERS = {
    "Authorization": f"Bearer {SYNAPSE_AUTH_TOKEN}",
    "Accept": "application/json"
}
# Function to fetch entity metadata
def get_entity_metadata(entity_id):
    ENTITY_API = f"{BASE_URL}/entity/{entity_id}"
    response = requests.get(ENTITY_API, headers=HEADERS)

    if response.status_code == 403:
        print(f"Access denied for entity {entity_id}. Check if you have the correct permissions.")
        return None
    response.raise_for_status()

    return response.json()

def get_file_versions(entity_id):
    VERSIONS_API = f"{BASE_URL}/entity/{entity_id}/version"
    response = requests.get(VERSIONS_API, headers=HEADERS)

    if response.status_code == 403:
        print(f"Access denied for file versions of {entity_id}")
        return {}
    response.raise_for_status()

    versions_data = response.json().get("results", [])

    file_md5_map = {}
    for version in versions_data:
        file_md5_map[f"{entity_id}.{version['versionNumber']}"] = version.get("contentMd5", "unknown_md5")

    return file_md5_map

# Function to fetch entities (child datasets)
def get_entities(parent_entity_id):
    ENTITY_API = f"{BASE_URL}/entity/{parent_entity_id}"
    response = requests.get(ENTITY_API, headers=HEADERS)

    if response.status_code == 403:
        print(f"Access denied for entity {parent_entity_id}.")
        return []
    response.raise_for_status()

    data = response.json()
    return [f"{item['entityId']}.{item['versionNumber']}" for item in data.get("items", [])]

# Function to fetch annotations
def get_annotations(entity_ids):
    annotations = []
    for entity in entity_ids:
        entity_id, _ = entity.split(".")  # Extract entityId
        response = requests.get(f"{BASE_URL}/entity/{entity_id}/annotations2", headers=HEADERS)

        if response.status_code == 403:
            print(f"Access denied for {entity_id}")
            continue
        elif response.status_code != 200:
            print(f"Failed to fetch annotations for {entity_id}: {response.status_code}")
            continue

        annotation_data = response.json()
        annotations.append({
            "synapse_id": entity,
            "annotations": annotation_data
        })
    return annotations

# Function to save data as a formatted JSON file
def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"File saved: {filename}")

# Function to convert annotations to Croissant metadata format
def convert_to_croissant(input_file, output_file, dataset_metadata,file_md5_map):
    # Load the input JSON file
    with open(input_file, "r") as file:
        annotations_data = json.load(file)

    # Extract dataset name, description, and URL from metadata
    dataset_name = dataset_metadata.get("name", "Synapse Dataset")
    dataset_description = dataset_metadata.get("description", "A dataset containing annotations for genomic data from Synapse.")
    dataset_id = dataset_metadata.get("id", "unknown_id")
    citation = dataset_metadata.get("citation","unknown_citation")
    datePublished = dataset_metadata.get("createdOn","unknown_date")
    dataset_license = dataset_metadata.get("license","unknown_license")
    version = dataset_metadata.get("versionNumber","unknown_citation")

    # Construct dataset URL
    dataset_url = f"https://www.synapse.org/Synapse:{dataset_id}"

    # Initialize Croissant metadata structure
    croissant_metadata = {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "citeAs": "cr:citeAs",
            "column": "cr:column",
            "conformsTo": "dct:conformsTo",
            "cr": "http://mlcommons.org/croissant/",
            "rai": "http://mlcommons.org/croissant/RAI/",
            "data": {
            "@id": "cr:data",
            "@type": "@json"
            },
            "dataType": {
            "@id": "cr:dataType",
            "@type": "@vocab"
            },
            "dct": "http://purl.org/dc/terms/",
            "examples": {
            "@id": "cr:examples",
            "@type": "@json"
            },
            "extract": "cr:extract",
            "field": "cr:field",
            "fileProperty": "cr:fileProperty",
            "fileObject": "cr:fileObject",
            "fileSet": "cr:fileSet",
            "format": "cr:format",
            "includes": "cr:includes",
            "isLiveDataset": "cr:isLiveDataset",
            "jsonPath": "cr:jsonPath",
            "key": "cr:key",
            "md5": "cr:md5",
            "parentField": "cr:parentField",
            "path": "cr:path",
            "recordSet": "cr:recordSet",
            "references": "cr:references",
            "regex": "cr:regex",
            "repeated": "cr:repeated",
            "replace": "cr:replace",
            "sc": "https://schema.org/",
            "separator": "cr:separator",
            "source": "cr:source",
            "subField": "cr:subField",
            "transform": "cr:transform"
        },
        "@type": "Dataset",
        "name": dataset_name,
        "description": dataset_description,
        "url": dataset_url,
        "citation": citation,
        "datePublished": datePublished,
        "license": dataset_license,
        "version": version,
        "distribution": [],
        "recordSet": []
    }

    for entry in annotations_data:
        file_id = entry["synapse_id"]
        file_md5 = file_md5_map.get(file_id, "unknown_md5")  # Get MD5 from mapping

        # Define FileObject for distribution
        file_object = {
            "@type": "FileObject",
            "@id": file_id,
            "name": file_id,
            "description": f"Data file associated with {file_id}",
            "contentUrl": f"https://www.synapse.org/Synapse:{file_id}",
            "encodingFormat": "application/json",
            "md5": file_md5  # Include MD5 hash
        }
        croissant_metadata["distribution"].append(file_object)

        # Define RecordSet with Fields
        record_set = {
            "@type": "RecordSet",
            "@id": f"record-{file_id}",
            "name": f"record-{file_id}",
            "field": [
                {
                    "@type": "Field",
                    "@id": f"{file_id}/{key}",
                    "name": key,
                    "dataType": "sc:Text",
                    "source": {
                        "fileObject": {"@id": file_id},
                        "extract": {"column": key}
                    }
                }
                for key in entry["annotations"]["annotations"].keys()
            ]
        }

        croissant_metadata["recordSet"].append(record_set)

    # Save the transformed Croissant metadata JSON file
    with open(output_file, "w") as file:
        json.dump(croissant_metadata, file, indent=4)

    print(f"Croissant metadata saved to {output_file}")

# Function to import dataset and generate Croissant metadata
def import_croissant(synapse_id):
    print(f"Processing Synapse dataset: {synapse_id}")

    # Fetch dataset metadata
    dataset_metadata = get_entity_metadata(synapse_id)
    if not dataset_metadata:
        print("Failed to fetch dataset metadata.")
        return

    # Fetch child entities
    entities = get_entities(synapse_id)

    # Fetch annotations
    annotations_data = get_annotations(entities)

    # Fetch file MD5 hashes for all entities
    file_md5_map = {}
    for entity in entities:
        entity_id, _ = entity.split(".")  # Extract entity ID
        file_md5_map.update(get_file_versions(entity_id))  # Merge MD5 hashes

    # Define filenames with Synapse ID prefix
    annotations_file = f"{synapse_id}_annotations.json"
    croissant_file = f"{synapse_id}_croissant_metadata.json"

    # Save to JSON file
    save_to_json(annotations_data, annotations_file)

    # Convert to Croissant metadata
    convert_to_croissant(annotations_file, croissant_file, dataset_metadata, file_md5_map)

# Example usage:
import_croissant("syn53132831")
import_croissant("syn52623570")
import_croissant("syn63645356")
import_croissant("syn11269541")
import_croissant("syn51732482")
import_croissant("syn4993293")

# https://repo-prod.prod.sagebase.org/repo/v1/entity/syn20503814/version
# md5
# citation
# data published
# license
# version
# Add files to synapse folder and annotate with

# isFeatured
# program
# name
# description
# contributors
# keywords
# individuals
# size
# sizeUnit
# dimensions
# includedInDataCatalog
# link
# license
# downloads
