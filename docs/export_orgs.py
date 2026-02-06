import json
from synapseclient import Synapse
from synapseclient.models.schema_organization import list_json_schema_organizations

syn = Synapse()
syn.login()

all_orgs = list_json_schema_organizations()
total_orgs = len(all_orgs)

print(f"Found {total_orgs} organizations.")

rows = []

for i, org in enumerate(all_orgs, start=1):
    # Try to show something useful for progress
    org_id = getattr(org, "id", "unknown")
    org_name = getattr(org, "name", "unknown")

    print(f"\n[{i}/{total_orgs}] Processing org: {org_id} ({org_name})")

    schemas = org.get_json_schemas()

    for schema in schemas:
        versions = schema.get_versions()

        for version in versions:
            rows.append({
                "organization_id": version.organization_id,
                "organization_name": version.organization_name,
                "schema_id": version.schema_id,
                "schema_name": version.schema_name,
                "version_id": version.version_id,
                "semantic_version": version.semantic_version,
                "created_on": version.created_on,
                "created_by": version.created_by,
                "json_sha256_hex": version.json_sha256_hex,
            })

    print(f"    Rows collected so far: {len(rows)}")

with open("docs/data.json", "w") as f:
    json.dump(rows, f, indent=2)

print(f"\nDone. Wrote {len(rows)} rows to docs/data.json")
