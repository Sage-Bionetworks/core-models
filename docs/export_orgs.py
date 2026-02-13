"""
export_orgs.py

Exports Synapse JSON Schema registry metadata into docs/data.json.

- Lists all schema organizations
- For each organization, fetches schemas
- For each schema, fetches ALL versions
- Writes ONE row per schema (LATEST version only) to docs/data.json

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
def fetch_latest_schema_version(schema):
    """
    Fetch all versions for one schema, return only the latest version row.
    Latest is determined by created_on.
    """
    versions = list(schema.get_versions())
    if not versions:
        return None

    # Pick newest by created_on
    latest = max(versions, key=lambda v: v.created_on or "")

    return {
        "organization_id": latest.organization_id,
        "organization_name": latest.organization_name,
        "schema_id": latest.schema_id,
        "schema_name": latest.schema_name,
        "version_id": latest.version_id,
        "semantic_version": latest.semantic_version,
        "created_on": latest.created_on,
        "created_by": latest.created_by,
        "json_sha256_hex": latest.json_sha256_hex,
    }


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
            futures.append(executor.submit(fetch_latest_schema_version, schema))

        for f in as_completed(futures):
            try:
                r = f.result()
                if r:
                    rows.append(r)
            except Exception as e:
                print(f"    WARNING: schema version fetch failed: {e}")

    print(f"    Rows collected so far: {len(rows)}")

os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(rows, f, indent=2)

print(
    f"\nDone. Processed {processed_orgs} org(s). "
    f"Wrote {len(rows)} rows to {OUTPUT_PATH} "
    f"(latest schema versions only)"
)