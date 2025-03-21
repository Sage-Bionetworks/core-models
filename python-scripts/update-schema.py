import synapseclient
import time
import json

syn = synapseclient.Synapse()
syn.login()

schemaRequestBody = """
{
  "schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered/sagedm-dataset",
    "type": "object",
    "properties": {
      "accessType": {
        "description": "Access type for the dataset.",
        "title": "Access Type",
        "enum": [
          "Public Access",
          "Open Access",
          "Controlled Access",
          "Private Access"
        ],
        "type": "string"
      },
      "alternateName": {
        "description": "An alternate name that can be used for search and discovery improvement.",
        "title": "Alternate Name",
        "type": "string"
      },
      "conditionsOfAccess": {
        "description": "Additional requirements a user may need outside of Data Use Modifiers. This could include additional registration, updating profile information, joining a Synapse Team, or using specific authentication methods like 2FA or RAS. Omit property if not applicable/unknown.",
        "title": "User Specific Restriction",
        "type": "string"
      },
      "contributor": {
        "description": "Organization(s) or person(s) that contributed to the dataset.",
        "type": "array",
        "items": {
          "type": "string"
        },
        "title": "Contributor(s)"
      },
      "countryOfOrigin": {
        "description": "Origin of individuals from which data were generated. Omit if not applicable/unknown.",
        "type": "array",
        "items": {
          "type": "string"
        },
        "title": "Country of Origin"
      },
      "creator": {
        "description": "Organization or person that is creator of the dataset. Default is the PI of the project and/or the user who created all files in the dataset.",
        "title": "Creator",
        "type": "string"
      },
      "dataUseModifiers": {
        "description": "List of data use ontology (DUO) terms that describe the allowable scope and terms for data use. Omit property if not applicable/unknown.",
        "type": "array",
        "items": {
          "enum": [
            "Clinical Care Use",
            "Collaboration Required",
            "Disease Specific Research",
            "Ethics Approval Required",
            "General Research Use",
            "Genetic Studies Only",
            "Geographical Restriction",
            "Health or Medical or Biomedical Research",
            "Institution Specific Restriction",
            "No General Methods Research",
            "No Restriction",
            "Not-for-Profit Non-Commercial Use Only",
            "Non-Commercial Use Only",
            "Not-for-Profit Organisation Use Only",
            "Population Origins or Ancestry Research Only",
            "Population Origins or Ancestry Research Prohibited",
            "Project Specific Restriction",
            "Publication Moratorium",
            "Publication Required",
            "Research Specific Restrictions",
            "Return to Database or Resource",
            "Time Limit on Use",
            "User Specific Restriction"
          ]
        },
        "title": "Data Use Modifiers"
      },
      "datePublished": {
        "description": "Date data were published/available on Synapse.",
        "title": "Date Published",
        "type": "string",
        "format": "date"
      },
      "funder": {
        "description": "Organizations funding the dataset.",
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "Children's Tumor Foundation",
            "Gilbert Family Foundation",
            "Neurofibromatosis Therapeutic Acceleration Program",
            "National Cancer Institute",
            "National Institute of Aging",
            "Bill and Melinda Gates Foundation",
            "American Association for Cancer Research",
            "Digital Medicine Society",
            "Independent",
            "Other"
          ]
        },
        "title": "Funder"
      },
      "includedInDataCatalog": {
        "description": "Link(s) to known data catalog(s) the dataset is included in.",
        "title": "Included In Data Catalog",
        "type": "string",
        "enum": [
          "https://www.synapse.org/DataCatalog:0"
        ]
      },
      "keywords": {
        "description": "Relevant keywords for dataset search and discovery.",
        "type": "array",
        "items": {
          "type": "string"
        },
        "title": "Keywords"
      },
      "license": {
        "description": "Unless information for license is clear, this should default to UNKNOWN.",
        "title": "License",
        "type": "string",
        "enum": [
          "UNKNOWN",
          "Public Domain",
          "CC-0",
          "ODC-PDDL",
          "CC-BY",
          "ODC-BY",
          "ODC-ODbL",
          "CC BY-SA",
          "CC BY-NC",
          "CC BY-ND",
          "CC BY-NC-SA",
          "CC BY-NC-ND"
        ]
      },
      "measurementTechnique": {
        "description": "Assay used to generate original data.",
        "title": "Measurement Technique",
        "type": "string"
      },
      "species": {
        "description": "Species of the organism(s) from which the data were generated. Omit property if not applicable.",
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "Human",
            "Rat",
            "Mouse",
            "Rabbit",
            "Monkey",
            "Fruit Fly",
            "Humanized Mouse",
            "Chicken"
          ]
        },
        "title": "Species"
      },
      "subject": {
        "description": "Applicable subject term(s) for dataset cataloging; use the Library of Congress Subject Headings (LCSH) scheme.",
        "type": "array",
        "items": {
          "type": "string"
        },
        "title": "Subject"
      },
      "title": {
        "title": "Title",
        "type": "string"
      }
    },
    "required": [
      "title",
      "creator",
      "keywords"
    ]
  },
  "dryRun": false
}
"""

# Issue a request to create the schema
schemaJobResponse = syn.restPOST("/schema/type/create/async/start", schemaRequestBody)

# Check on the job until it completes.
asyncJobStatus = syn.restGET(f"/asynchronous/job/{schemaJobResponse['token']}")

while asyncJobStatus["jobState"] == "PROCESSING":
    time.sleep(1)
    asyncJobStatus = syn.restGET(f"/asynchronous/job/{schemaJobResponse['token']}")
