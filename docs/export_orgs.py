"""
export_orgs.py

Exports Synapse JSON Schema registry metadata into docs/data.json.

- Lists all schema organizations
- Fetches all org schema lists in parallel (Phase 1)
- Fetches latest version for every schema in parallel (Phase 2)
- Writes ONE row per schema (LATEST version only) to docs/data.json

Adds:
  - status field: "published" or "draft"

Environment variables:
  SYNAPSE_AUTH_TOKEN  - Required. Synapse personal access token.

Optional:
  ORG_NAME_FILTER     - If set (e.g. "ADA.PSI"), only export that org.
                        If blank/unset, exports all orgs.
  MAX_WORKERS         - Number of concurrent threads (default: 16)
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
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "16"))
ORG_NAME_FILTER = os.environ.get("ORG_NAME_FILTER", "").strip()
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "docs/data.json")

# Organizations that should be marked as "published"
PUBLISHED_ORGS = {
    "MC2Center",
    "org.synapse.nf",
    "HTAN2Organization"
}


# ──────────────────────────────────────────────
# Synapse login
# ──────────────────────────────────────────────
syn = Synapse()
syn.login(authToken=os.environ.get("SYNAPSE_AUTH_TOKEN"), silent=True)


# ──────────────────────────────────────────────
# Phase 1 — fetch schema list for one org
# ──────────────────────────────────────────────
def fetch_org_schemas(org):
    org_name = getattr(org, "name", "unknown")
    org_id = getattr(org, "id", "unknown")
    if ORG_NAME_FILTER and org_name != ORG_NAME_FILTER:
        return []
    try:
        schemas = list(org.get_json_schemas())
        print(f"  org {org_id} ({org_name}): {len(schemas)} schemas")
        return schemas
    except Exception as e:
        print(f"  ERROR fetching schemas for org {org_name}: {e}")
        return []


# ──────────────────────────────────────────────
# Phase 2 — fetch latest version for one schema
# ──────────────────────────────────────────────
def fetch_latest_schema_version(schema):
    try:
        versions = list(schema.get_versions())
        if not versions:
            return None

        latest = max(versions, key=lambda v: v.created_on or "")

        status = "published" if latest.organization_name in PUBLISHED_ORGS else "draft"

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
            "status": status,
        }

    except Exception as e:
        print(f"  ERROR fetching versions for schema: {e}")
        return None


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    all_orgs = list_json_schema_organizations()
    total_orgs = len(all_orgs)
    print(f"Found {total_orgs} organizations. Using {MAX_WORKERS} workers.\n")

    # ── Phase 1: fetch all schema lists in parallel ──
    print("Phase 1: fetching schema lists for all orgs...")
    all_schemas = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_org_schemas, org): org for org in all_orgs}
        for f in as_completed(futures):
            all_schemas.extend(f.result())

    total_schemas = len(all_schemas)
    print(f"\nPhase 1 done. {total_schemas} schemas found across all orgs.\n")

    if not all_schemas:
        print("No schemas to process. Exiting.")
        return

    # ── Phase 2: fetch latest version for every schema in parallel ──
    print("Phase 2: fetching latest version for each schema...")
    rows = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_latest_schema_version, schema): schema
            for schema in all_schemas
        }
        done = 0
        for f in as_completed(futures):
            result = f.result()
            if result:
                rows.append(result)
            done += 1
            if done % 50 == 0 or done == total_schemas:
                print(f"  {done}/{total_schemas} schemas processed, {len(rows)} rows collected")

    print(f"\nPhase 2 done.")

    # ── Write output ──
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"\nDone. Wrote {len(rows)} rows to {OUTPUT_PATH} (latest schema versions only)")


if __name__ == "__main__":
    main()
