"""
import_to_coremodels.py

Reads docs/data.json, fetches each unique schema from the Synapse registry,
and imports it into CoreModels via the Merge JSON Schema API.

NEW:
  - Only imports schemas where status == "published"

Required environment variables:
  COREMODELS_API_URL        - Base URL for CoreModels API (e.g. https://api.coremodels.io)
  COREMODELS_API_TOKEN      - Bearer token for CoreModels
  COREMODELS_PROJECT_ID     - CoreModels project ID
  COREMODELS_SPACE_ID       - Target space ID to import into
  COREMODELS_CONFIG_TYPE_ID - JSON Schema import profile ID

Optional:
  ORG_NAME_FILTER           - Organization name to filter imports (e.g. "ADA.PSI")
                              If blank or unset, imports all organizations.
  OVERRIDE_NEW_PROPERTIES   - "true" to skip unmapped properties warning (default: "true")
  OVERRIDE_DIFFERENT_SOURCE - "true" to skip different source warning (default: "true")
  OVERRIDE_OVERWRITE        - "true" to skip overwrite warning (default: "true")
  ONLY_ADD_AND_UPDATE       - "true" to only add/update, never remove (default: "true")
  DRY_RUN                   - "true" to only list schemas without importing (default: "false")
  DATA_JSON_PATH            - Path to docs/data.json (default: "docs/data.json")
  RATE_LIMIT_SECONDS        - Seconds to wait between API calls PER WORKER (default: "0.0")
  MAX_WORKERS               - Thread workers for parallel import (default: "8")
  VERIFY_URLS               - "true" to pre-check schema URLs (default: "false")
  BATCH_SIZE                - Number of schemas to import in each batch (default: "20")
"""

import json
import os
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


# ──────────────────────────────────────────────
# Configuration from environment
# ──────────────────────────────────────────────
API_URL = os.environ.get("COREMODELS_API_URL", "").rstrip("/")
API_TOKEN = os.environ.get("COREMODELS_API_TOKEN", "")
PROJECT_ID = os.environ.get("COREMODELS_PROJECT_ID", "")
SPACE_ID = os.environ.get("COREMODELS_SPACE_ID", "")
CONFIG_TYPE_ID = os.environ.get("COREMODELS_CONFIG_TYPE_ID", "")

ORG_NAME_FILTER = os.environ.get("ORG_NAME_FILTER", "").strip()

OVERRIDE_NEW_PROPS = os.environ.get("OVERRIDE_NEW_PROPERTIES", "true").lower() == "true"
OVERRIDE_DIFF_SRC = os.environ.get("OVERRIDE_DIFFERENT_SOURCE", "true").lower() == "true"
OVERRIDE_OVERWRITE = os.environ.get("OVERRIDE_OVERWRITE", "true").lower() == "true"
ONLY_ADD_UPDATE = os.environ.get("ONLY_ADD_AND_UPDATE", "true").lower() == "true"
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

DATA_JSON_PATH = os.environ.get("DATA_JSON_PATH", "docs/data.json")

RATE_LIMIT_SECONDS = float(os.environ.get("RATE_LIMIT_SECONDS", "0.0"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "1"))
VERIFY_URLS = os.environ.get("VERIFY_URLS", "false").lower() == "true"
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "20"))

SYNAPSE_SCHEMA_BASE = "https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def validate_config():
    missing = []
    if not API_URL:
        missing.append("COREMODELS_API_URL")
    if not API_TOKEN:
        missing.append("COREMODELS_API_TOKEN")
    if not PROJECT_ID:
        missing.append("COREMODELS_PROJECT_ID")
    if not SPACE_ID:
        missing.append("COREMODELS_SPACE_ID")
    if not CONFIG_TYPE_ID:
        missing.append("COREMODELS_CONFIG_TYPE_ID")

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


def load_data_json(path):
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run export_orgs.py first.")
        sys.exit(1)

    with open(path, "r") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} rows from {path}")
    return data


def filter_data_by_org_name(data):
    if not ORG_NAME_FILTER:
        print("ORG_NAME_FILTER not set — importing schemas from ALL organizations")
        return data

    filtered = [row for row in data if row.get("organization_name") == ORG_NAME_FILTER]

    print(
        f"ORG_NAME_FILTER='{ORG_NAME_FILTER}' — "
        f"kept {len(filtered)} of {len(data)} rows"
    )

    if not filtered:
        print(
            f"WARNING: No rows matched organization_name='{ORG_NAME_FILTER}'. "
            f"Nothing will be imported."
        )

    return filtered


def filter_data_by_status_published(data):
    """
    Keep only rows where status == "published".
    If status is missing, treat it as draft.
    """
    published = []
    for row in data:
        status = (row.get("status") or "").strip().lower()
        if status == "published":
            published.append(row)

    print(f"Status filter: kept {len(published)} published rows out of {len(data)} total")
    return published


def get_unique_schemas(data):
    """
    Extract unique (organization_name, schema_name) pairs.
    Even though export now writes only latest versions,
    we still deduplicate for safety.
    """
    seen = set()
    unique = []

    for row in data:
        org = row.get("organization_name", "")
        schema = row.get("schema_name", "")
        if not org or not schema:
            continue

        key = f"{org}-{schema}"
        if key in seen:
            continue

        seen.add(key)
        unique.append(
            {
                "organization_name": org,
                "schema_name": schema,
                "key": key,
            }
        )

    print(f"Found {len(unique)} unique schemas to import")
    return unique


def build_synapse_schema_url(org_name, schema_name):
    return f"{SYNAPSE_SCHEMA_BASE}/{org_name}-{schema_name}"


def verify_schema_url(url):
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            resp.json()
            return True
        print(f"  WARNING: Schema URL returned HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"  WARNING: Could not verify schema URL: {e}")
        return False


def batch_import_schema_to_coremodels(schema_urls, session: requests.Session):
    endpoint = f"{API_URL}/v1/{PROJECT_ID}/mergeJSONSchema"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body = {
        "spaceId": SPACE_ID,
        "configTypeId": CONFIG_TYPE_ID,
        "sourceDtos": [{"fileUrl": url} for url in schema_urls],
        "overrideNewPropertiesWarning": OVERRIDE_NEW_PROPS,
        "overrideDifferentSourceWarning": OVERRIDE_DIFF_SRC,
        "overrideOverwriteWarning": OVERRIDE_OVERWRITE,
        "onlyAddAndUpdate": ONLY_ADD_UPDATE,
    }

    try:
        resp = session.post(endpoint, headers=headers, json=body, timeout=120)

        if resp.status_code == 200:
            result = resp.json()
            if result.get("success"):
                return True, None
            error = result.get("error", {})
            msg = error.get("message", "Unknown error")
            fatal = error.get("isFatal", False)
            return False, f"{msg} (fatal={fatal})"

        return False, f"HTTP {resp.status_code}: {resp.text[:300]}"

    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except Exception as e:
        return False, f"Exception: {e}"

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("CoreModels Schema Import")
    print("=" * 60)

    if DRY_RUN:
        print("🔍 DRY RUN MODE — no imports will be performed\n")
    else:
        print()

    validate_config()

    print(f"API URL:        {API_URL}")
    print(f"Project ID:     {PROJECT_ID}")
    print(f"Space ID:       {SPACE_ID}")
    print(f"Config Type ID: {CONFIG_TYPE_ID}")
    print(f"Org filter:     {ORG_NAME_FILTER if ORG_NAME_FILTER else '(none)'}")
    print("Status filter:  published only")
    print(f"Max workers:    {MAX_WORKERS}")
    print(f"Verify URLs:    {VERIFY_URLS}")
    print(f"Rate limit:     {RATE_LIMIT_SECONDS} seconds/worker")
    print(
        f"Override flags: new_props={OVERRIDE_NEW_PROPS}, "
        f"diff_src={OVERRIDE_DIFF_SRC}, overwrite={OVERRIDE_OVERWRITE}, "
        f"add_update_only={ONLY_ADD_UPDATE}"
    )
    print()

    data = load_data_json(DATA_JSON_PATH)
    data = filter_data_by_org_name(data)
    data = filter_data_by_status_published(data)   # ← NEW FILTER
    schemas = get_unique_schemas(data)

    if not schemas:
        print("No published schemas found to import. Exiting.")
        sys.exit(0)

    print(f"\nStarting parallel import with {MAX_WORKERS} workers...\n")

    lock = Lock()
    success_count = 0
    fail_count = 0
    skip_count = 0
    failed_schemas = []

    def process_schema_batch(batch):
        batch_keys = [s["key"] for s in batch]
        urls = []
        for i, schema in enumerate(batch):
            org = schema["organization_name"]
            name = schema["schema_name"]
            url = build_synapse_schema_url(org, name)
            
            if VERIFY_URLS and not verify_schema_url(url):
                print(f"    ⏭️  Skipping {schema['key']} — URL not accessible: {url}")
                continue

            urls.append(url)

        if DRY_RUN:
            print(f"  ⏭️  Skipped batch {batch_keys} (dry run)")
            return ("skip", batch_keys, None)

        if not urls:
            print(f"  ⏭️  Skipped batch {batch_keys} — no valid URLs")
            return ("skip", batch_keys, "All URLs failed verification")
        
        with requests.Session() as session:
            ok, reason = batch_import_schema_to_coremodels(urls, session)

        if RATE_LIMIT_SECONDS > 0:
            time.sleep(RATE_LIMIT_SECONDS)

        if ok:
            print(f"  ✅ Successfully imported batch")
            return ("success", batch_keys, None)

        print(f"  ❌ Import failed: {reason}")
        return ("fail", batch_keys, reason)
            
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_schema_batch, schemas[i:i+BATCH_SIZE])
            for i in range(0, len(schemas), BATCH_SIZE)
        ]

        for f in as_completed(futures):
            result, key, reason = f.result()

            with lock:
                if result == "success":
                    success_count += 1
                elif result == "fail":
                    fail_count += 1
                    failed_schemas.append({"key": key, "reason": reason})
                elif result == "skip":
                    skip_count += 1
                    if reason:
                        failed_schemas.append({"key": key, "reason": reason})

    # ──────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"  Total batches:  {len(schemas)}")
    print(f"  ✅ Succeeded:   {success_count}")
    print(f"  ❌ Failed:      {fail_count}")
    print(f"  ⏭️  Skipped:    {skip_count}")

    if failed_schemas:
        print("\nFailed/skipped batches:")
        for f in failed_schemas:
            print(f"  - {f['key']}: {f['reason']}")

    if fail_count > 0:
        print(f"\n⚠️  {fail_count} batch(es) failed to import.")
        sys.exit(1)

    print("\n🎉 All published batches processed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()