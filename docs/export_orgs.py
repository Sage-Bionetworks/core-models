import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from synapseclient import Synapse
from synapseclient.models.schema_organization import list_json_schema_organizations

MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "12"))
ORG_NAME_FILTER = os.environ.get("ORG_NAME_FILTER", "").strip()

syn = Synapse()
syn.login(authToken=os.environ.get("SYNAPSE_AUTH_TOKEN"), silent=True)

all_orgs = list_json_schema_organizations()
total_orgs = len(all_orgs)

print(f"Found {total_orgs} organizations.")

def fetch_schema_versions(org_id, org_name, schema):
    """Fetch all versions for one schema and return rows."""
    rows = []
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

    return rows


rows = []

for i, org in enumerate(all_orgs, start=1):
    org_id = getattr(org, "id", "unknown")
    org_name = getattr(org, "name", "unknown")

    if ORG_NAME_FILTER and org_name != ORG_NAME_FILTER:
        continue

    print(f"\n[{i}/{total_orgs}] Processing org: {org_id} ({org_name})")

    schemas = org.get_json_schemas()
    print(f"    Found {len(schemas)} schemas")

    futures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for schema in schemas:
            futures.append(executor.submit(fetch_schema_versions, org_id, org_name, schema))

        for f in as_completed(futures):
            try:
                rows.extend(f.result())
            except Exception as e:
                print(f"    WARNING: schema version fetch failed: {e}")

    print(f"    Rows collected so far: {len(rows)}")

os.makedirs("docs", exist_ok=True)

with open("docs/data.json", "w") as f:
    json.dump(rows, f, indent=2)

print(f"\nDone. Wrote {len(rows)} rows to docs/data.json")
