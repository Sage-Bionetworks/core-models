import synapseclient
import time
import json

syn = synapseclient.Synapse()
syn.login()

objectId = 'syn64720225' # Replace the ID with your own

jsonSchemaObjectBinding = f"""{{ "entityId": "{objectId}", "schema$id": "sagedm-dataset"}}"""

syn.restPUT(f"/entity/{objectId}/schema/binding", jsonSchemaObjectBinding)