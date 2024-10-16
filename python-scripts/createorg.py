import synapseclient
import json

# Log in to Synapse
syn = synapseclient.Synapse()
syn.login()

# Define your unique organization name
organization_name = "SageCoreModels"

# Create the request body with the organization name
organization_request_body = {
    "organizationName": organization_name
}

# Create the organization via REST API
try:
    organization = syn.restPOST("/schema/organization", json.dumps(organization_request_body))
    print(f"Organization '{organization_name}' created successfully!")
except Exception as e:
    print(f"Failed to create organization: {e}")