import synapseclient
import time  # Import the time module for sleeping between status checks
import json  # Import json to handle JSON objects

syn = synapseclient.Synapse()
syn.login()

schemaRequestBody = """
{
  "schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered/SageCoreModels-Dataset",
    "properties": {
      "alternateName": {
        "type": "string",
        "description": "An alternative name for the dataset."
      },
      "includedInDataCatalog": {
        "type": "string",
        "description": "The data catalog that includes this dataset."
      },
      "keywords": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Keywords or tags associated with the dataset."
      },
      "measurementTechnique": {
        "description": "The technique or technology used to measure the data.",
        "enum": [
          "ATAC-seq",
          "CAPP-seq",
          "ChIP-seq",
          "CUT&RUN",
          "ERR bisulfite sequencing",
          "HI-C",
          "ISO-seq",
          "lncRNA-seq",
          "miRNA-seq",
          "NOMe-seq",
          "oxBS-seq",
          "ribo-seq",
          "RNA-seq",
          "SaferSeqS",
          "scCGI-seq",
          "single cell ATAC-seq",
          "single-cell RNA-seq",
          "single-nucleus RNA-seq",
          "SNP array",
          "targeted exome sequencing",
          "T cell receptor repertoire sequencing",
          "whole exome sequencing",
          "whole genome sequencing",
          "3D confocal imaging",
          "3D electron microscopy",
          "3D imaging",
          "atomic force microscopy",
          "brightfield microscopy",
          "confocal microscopy",
          "electron microscopy",
          "fluorescence in situ hybridization (FISH)",
          "functional MRI",
          "high frequency ultrasound",
          "in vivo bioluminescence",
          "in vivo PDX viability",
          "in vivo tumor growth",
          "laser speckle imaging",
          "magnetic resonance spectroscopy",
          "MRI",
          "optical coherence tomography",
          "optical tomography",
          "optokinetic reflex assay",
          "pattern electroretinogram",
          "PET (positron emission tomography)",
          "phase-contrast microscopy",
          "spatial frequency domain imaging",
          "spatial transcriptomics"
        ],
        "type": "string"
      },
      "dateModified": {
        "type": "integer",
        "description": "The date on which the dataset was last modified."
      },
      "dateCreated": {
        "type": "integer",
        "description": "The date on which the dataset was created."
      },
      "creator": {
        "type": "string",
        "description": "The creator of the dataset."
      },
      "funding": {
        "type": "string",
        "description": "The funding source for the dataset."
      },
      "isPartOf": {
        "type": "string",
        "description": "The data repository or portal to which this dataset belongs.",
        "enum": [
          "NF Data Portal"
        ]
      },
      "conditionsOfAccess": {
        "type": "string",
        "description": "Conditions of access for the dataset."
      },
      "citation": {
        "type": "string",
        "description": "Citation details for the dataset."
      }
    },
    "required": [
      "includedInDataCatalog",
      "keywords"
    ]
  }
}

"""

# Issue a request to create the schema
schemaJobResponse = syn.restPOST("/schema/type/create/async/start", schemaRequestBody)

# Check on the job until it completes.
asyncJobStatus = syn.restGET(f"/asynchronous/job/{schemaJobResponse['token']}")

while asyncJobStatus["jobState"] == "PROCESSING":
    time.sleep(1)
    asyncJobStatus = syn.restGET(f"/asynchronous/job/{schemaJobResponse['token']}")

objectId = 'syn59401810' # Replace the ID with your own

jsonSchemaObjectBinding = f"""{{ "entityId": "{objectId}", "schema$id": "SageCoreModels-Dataset"}}"""

syn.restPUT(f"/entity/{objectId}/schema/binding", jsonSchemaObjectBinding)