"""
export_orgs.py

Exports Synapse JSON Schema registry metadata into public/data.json.

- Lists all schema organizations
- Fetches all org schema lists in parallel (Phase 1)
- Fetches latest version for every schema in parallel (Phase 2)
- Writes ONE row per schema (LATEST version only) to public/data.json

Adds:
  - status field: "published" or "draft"

Environment variables:
  SYNAPSE_AUTH_TOKEN  - Required. Synapse personal access token.

Optional:
  ORG_NAME_FILTER     - If set (e.g. "ADA.PSI"), only export that org.
                        If blank/unset, exports all orgs.
  MAX_WORKERS         - Number of concurrent threads (default: 16)
  OUTPUT_PATH         - Output file path (default: public/data.json)
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from synapseclient import Synapse
from synapseclient.models.schema_organization import list_json_schema_organizations


# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "32"))
ORG_NAME_FILTER = os.environ.get("ORG_NAME_FILTER", "").strip()
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "public/data.json")

# Organizations that should be marked as "published"
PUBLISHED_ORGS = {
    "MC2Center",
    "org.synapse.nf",
    "HTAN2Organization",
    "sage.schemas.ad",
    "sage.schemas.elite",
    "NAMhub",
    "org.synapse.classic"
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
def list_all_versions(org_name, schema_name):
    """Return every registered version of a schema as raw dicts.

    Uses the /schema/version/list REST endpoint directly instead of
    schema.get_versions(), because the synapseclient wrapper silently
    drops any version that has no semantic version (it filters on
    `if "semanticVersion" in schema`). Schemas registered without a
    x.y.z semantic version therefore never reach data.json, even though
    they are fully registered and resolvable in Synapse. Paginated.
    """
    body = {"organizationName": org_name, "schemaName": schema_name}
    versions = []
    while True:
        resp = syn.restPOST("/schema/version/list", body=json.dumps(body))
        versions.extend(resp.get("page", []))
        next_token = resp.get("nextPageToken")
        if not next_token:
            return versions
        body["nextPageToken"] = next_token


def fetch_latest_schema_version(schema, cached=None):
    try:
        versions = list_all_versions(schema.organization_name, schema.name)
        if not versions:
            return None

        latest = max(versions, key=lambda v: v.get("createdOn") or "")

        org_name = latest.get("organizationName")
        schema_name = latest.get("schemaName")
        sha256 = latest.get("jsonSHA256Hex")
        # semanticVersion is absent for schemas registered without a x.y.z tag.
        semantic_version = latest.get("semanticVersion")
        status = "published" if org_name in PUBLISHED_ORGS else "draft"

        # If SHA256 matches the cached value, return the cached row unchanged
        key = f"{org_name}-{schema_name}"
        if cached and sha256 and cached.get(key) == sha256:
            return {"_cached": True, "organization_id": latest.get("organizationId"),
                    "organization_name": org_name,
                    "schema_id": latest.get("schemaId"), "schema_name": schema_name,
                    "version_id": latest.get("versionId"), "semantic_version": semantic_version,
                    "created_on": latest.get("createdOn"), "created_by": latest.get("createdBy"),
                    "json_sha256_hex": sha256,
                    "status": status}

        return {
            "organization_id": latest.get("organizationId"),
            "organization_name": org_name,
            "schema_id": latest.get("schemaId"),
            "schema_name": schema_name,
            "version_id": latest.get("versionId"),
            "semantic_version": semantic_version,
            "created_on": latest.get("createdOn"),
            "created_by": latest.get("createdBy"),
            "json_sha256_hex": sha256,
            "status": status,
        }

    except Exception as e:
        print(f"  ERROR fetching versions for schema: {e}")
        return None


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def load_existing_sha256s(path):
    """Return a dict of {org-schema key: json_sha256_hex} from the existing data.json."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        return {
            f"{r['organization_name']}-{r['schema_name']}": r.get("json_sha256_hex", "")
            for r in data if r.get("organization_name") and r.get("schema_name")
        }
    except Exception:
        return {}


def main():
    # Load cached SHA256s so Phase 2 can skip unchanged schemas
    cached = load_existing_sha256s(OUTPUT_PATH)
    print(f"Loaded {len(cached)} cached schema SHA256s from {OUTPUT_PATH}\n")

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
    skipped = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_latest_schema_version, schema, cached): schema
            for schema in all_schemas
        }
        done = 0
        for f in as_completed(futures):
            result = f.result()
            if result:
                if result.get("_cached"):
                    skipped += 1
                    result.pop("_cached", None)
                rows.append(result)
            done += 1
            if done % 50 == 0 or done == total_schemas:
                print(f"  {done}/{total_schemas} processed  ({skipped} unchanged, {len(rows)-skipped} fetched)")

    print(f"\nPhase 2 done. {skipped}/{len(rows)} schemas were unchanged (skipped API detail call).")

    # ── Write output only if content changed ──
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    rows_sorted = sorted(rows, key=lambda r: (r.get("organization_name",""), r.get("schema_name","")))
    new_content = json.dumps(rows_sorted, indent=2)

    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            old_content = f.read()
        if old_content.strip() == new_content.strip():
            print(f"\nNo changes detected — {OUTPUT_PATH} is already up to date. Skipping write.")
            return

    with open(OUTPUT_PATH, "w") as f:
        f.write(new_content)

    print(f"\nDone. Wrote {len(rows)} rows to {OUTPUT_PATH} (latest schema versions only)")


if __name__ == "__main__":
    main()
