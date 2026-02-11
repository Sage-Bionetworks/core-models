"""
export_orgs.py

Exports Synapse JSON Schema registry metadata into docs/data.json.

- Lists all schema organizations
- For each organization, fetches schemas
- For each schema, fetches ALL versions
- Writes one row per schema version to docs/data.json

Environment variables:
  SYNAPSE_AUTH_TOKEN  - Required. Synapse personal access token.

Optional:
  ORG_NAME_FILTER     - If set (e.g. "ADA.PSI"), only export that org.
                        If blank/unset, exports all orgs.
  MAX_WORKERS         - Number of threads used to fetch schema versions (default: 12)
  OUTPUT_PATH         - Output file path (default: docs/data.json)
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from synapseclient import Synapse
from synapseclient.models.schema_organization import list_json_schema_organizations


# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "12"))
ORG_NAME_FILTER = os.environ.get("ORG_NAME_FILTER", "").strip()
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "docs/data.json")


# ──────────────────────────────────────────────
# Synapse login
# ──────────────────────────────────────────────
syn = Synapse()
syn.login(authToken=os.environ.get("SYNAPSE_AUTH_TOKEN"), silent=True)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def fetch_schema_versions(schema):
    """
    Fetch all versions for one schema and return rows.
    NOTE: schema.get_versions() may return a generator.
    """
    rows = []
    versions = schema.get_versions()

    for version in versions:
        rows.append(
            {
                "organization_id": version.organization_id,
                "organization_name": version.organization_name,
                "schema_id": version.schema_id,
                "schema_name": version.schema_name,
                "version_id": version.version_id,
                "semantic_version": version.semantic_version,
                "created_on": version.created_on,
                "created_by": version.created_by,
                "json_sha256_hex": version.json_sha256_hex,
            }
        )

    return rows


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
all_orgs = list_json_schema_organizations()
total_orgs = len(all_orgs)

print(f"Found {total_orgs} organizations.")

rows = []
processed_orgs = 0

for i, org in enumerate(all_orgs, start=1):
    org_id = getattr(org, "id", "unknown")
    org_name = getattr(org, "name", "unknown")

    if ORG_NAME_FILTER and org_name != ORG_NAME_FILTER:
        continue

    processed_orgs += 1
    print(f"\n[{i}/{total_orgs}] Processing org: {org_id} ({org_name})")

    # org.get_json_schemas() returns a generator → convert to list
    schemas = list(org.get_json_schemas())
    print(f"    Found {len(schemas)} schemas")

    if not schemas:
        continue

    futures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for schema in schemas:
            futures.append(executor.submit(fetch_schema_versions, schema))

        for f in as_completed(futures):
            try:
                rows.extend(f.result())
            except Exception as e:
                print(f"    WARNING: schema version fetch failed: {e}")

    print(f"    Rows collected so far: {len(rows)}")

os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(rows, f, indent=2)

print(
    f"\nDone. Processed {processed_orgs} org(s). "
    f"Wrote {len(rows)} rows to {OUTPUT_PATH}"
)
