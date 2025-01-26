import synapseclient
import pandas as pd
import json

# Login to Synapse securely
syn = synapseclient.Synapse()
syn.login()

try:
    # Load the dataset from Synapse
    query = syn.tableQuery("SELECT * FROM syn50913342")
    df = query.asDataFrame()

    # Initialize list to collect all graph entries
    graph_entries = []

    # Define the catalog enumeration for the data catalog
    catalog_enum = {
        "@type": "DataCatalog",
        "@id": "Sage Bionetworks"
    }
    graph_entries.append(catalog_enum)

    # Function to map each row to JSON-LD formatted dictionaries
    def row_to_jsonld(row):
        keywords = row['diseaseFocus'] if pd.notna(row['diseaseFocus']) else "TBD"
        description = row['description'] if pd.notna(row['description']) else "TBD"

        funding_id = row.get('fundingAgency')
        if pd.notna(funding_id):
            dataset_entry = {
                "@type": "Dataset",
                "@id": str(row['id']),
                "name": row['title'],
                "description": description,
                "alternateName": "To Be Determined",
                "includedInDataCatalog": {"@id": "Sage Bionetworks"},
                "keywords": keywords,
                "measurementTechnique": row['dataType'] if pd.notna(row['dataType']) else "TBD",
                "dateModified": pd.to_datetime(row['modifiedOn'], unit='ms', errors='coerce').strftime('%Y-%m-%d') if pd.notna(row['modifiedOn']) else "TBD",
                "dateCreated": int(row['yearProcessed']) if pd.notna(row['yearProcessed']) else "TBD",
                "funding": {"@type": "Organization", "@id": funding_id},
                "conditionsOfAccess": "To Be Determined",
                "citation": "To Be Determined"
            }
            graph_entries.append(dataset_entry)

            # Organization entry is only added if it does not already exist
            org_entry = {"@type": "Organization", "@id": funding_id}
            if org_entry not in graph_entries:
                graph_entries.append(org_entry)

    # Apply the function to each row
    df.apply(row_to_jsonld, axis=1)

    # Final JSON-LD structure
    jsonld_final = {
        "@context": {"schema": "http://schema.org/"},
        "@graph": graph_entries
    }

    # Saving the JSON-LD output
    filename = 'dataset.jsonld'
    with open(filename, 'w') as f:
        json.dump(jsonld_final, f, indent=4)

except Exception as e:
    print(f"An error occurred: {e}")
