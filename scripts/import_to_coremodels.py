"""
import_to_coremodels.py

Reads public/data.json, fetches each unique schema from the Synapse registry,
and imports it into CoreModels via the Merge JSON Schema API.

NEW:
  - Only imports schemas where status == "published"

Required environment variables:
  COREMODELS_API_URL        - Base URL for CoreModels API (e.g. https://api.coremodels.io)
  COREMODELS_API_TOKEN      - Bearer token for CoreModels
  COREMODELS_PROJECT_ID     - CoreModels project ID
  COREMODELS_SPACE_ID       - Target space ID to import into

Optional:
  COREMODELS_CONFIG_TYPE_ID - JSON Schema import profile ID. Leave empty/unset to let
                              CoreModels auto-select the default profile (recommended;
                              survives profile-id migrations). CoreModels v3.9.0 changed
                              the default profile id to d7cf1119ad8b84b8e3a122e5a64d006e.
  ORG_NAME_FILTER           - Organization name to filter imports (e.g. "ADA.PSI")
                              If blank or unset, imports all organizations.
  OVERRIDE_NEW_PROPERTIES   - "true" to skip unmapped properties warning (default: "true")
  OVERRIDE_DIFFERENT_SOURCE - "true" to skip different source warning (default: "true")
  OVERRIDE_OVERWRITE        - "true" to skip overwrite warning (default: "true")
  ONLY_ADD_AND_UPDATE       - "true" to only add/update, never remove (default: "true")
  DRY_RUN                   - "true" to only list schemas without importing (default: "false")
  DATA_JSON_PATH            - Path to public/data.json (default: "public/data.json")
  VERIFY_URLS               - "true" to pre-check schema URLs (default: "false")
  POLL_INTERVAL_SECONDS     - Seconds between job status checks (default: "60")
  JOB_TIMEOUT_SECONDS       - Max seconds to wait for a job before failing (default: "3600")
"""

import json
import os
import sys
import time
import requests


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
ONLY_ADD_UPDATE = os.environ.get("ONLY_ADD_AND_UPDATE", "false").lower() == "true"
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

DATA_JSON_PATH = os.environ.get("DATA_JSON_PATH", "public/data.json")

VERIFY_URLS = os.environ.get("VERIFY_URLS", "false").lower() == "true"
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "15"))
JOB_TIMEOUT_SECONDS = int(os.environ.get("JOB_TIMEOUT_SECONDS", "3600"))

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
    # COREMODELS_CONFIG_TYPE_ID is intentionally NOT required: when empty, CoreModels
    # auto-selects the default import profile (see queue_merge_job).

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


def queue_merge_job(schema_urls, session: requests.Session):
    endpoint = f"{API_URL}/v1/{PROJECT_ID}/queueMergeJSONSchema"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body = {
        "spaceId": SPACE_ID,
        # None → JSON null tells CoreModels to auto-select the default import profile.
        # The profile id changed in CoreModels v3.9.0, so pinning a stale id fails;
        # auto-select (empty CONFIG_TYPE_ID) is the resilient default.
        "configTypeId": CONFIG_TYPE_ID or None,
        "sourceDtos": [{"fileUrl": url} for url in schema_urls],
        "overrideNewPropertiesWarning": OVERRIDE_NEW_PROPS,
        "overrideDifferentSourceWarning": OVERRIDE_DIFF_SRC,
        "overrideOverwriteWarning": OVERRIDE_OVERWRITE,
        "onlyAddAndUpdate": ONLY_ADD_UPDATE,
    }

    try:
        resp = session.post(endpoint, headers=headers, json=body, timeout=600)

        if resp.status_code == 200:
            job_id = resp.json().get("data")
            if not job_id:
                return None, "Response did not include a jobId"
            return job_id, None

        return False, f"HTTP {resp.status_code}: {resp.text[:300]}"

    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except Exception as e:
        return False, f"Exception: {e}"

def wait_for_job(job_id: str, session: requests.Session):
    """
    Poll jobStatus every POLL_INTERVAL_SECONDS until the job completes or times out.
    Returns (success: bool, error_message: str | None).
    """
    endpoint = f"{API_URL}/v1/{PROJECT_ID}/jobStatus/{job_id}"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
    }

    elapsed = 0
    while elapsed < JOB_TIMEOUT_SECONDS:
        try:
            resp = session.get(
                endpoint,
                headers=headers,
                timeout=30
            )

            if resp.status_code != 200:
                return False, f"Status check HTTP {resp.status_code}: {resp.text[:300]}"

            data = resp.json().get("data")
            status = (data.get("status") or "").strip().lower()

            print(f"    [{elapsed}s] Job {job_id} — status: {status}")

            if status == "success":
                return True, None
            elif status == "failed":
                # The failure detail's location in the payload varies and is often
                # absent from `error`, which produced the useless "No error details
                # provided." message. Surface the ENTIRE jobStatus data object so the
                # real server-side reason (validation error, duplicate identifier,
                # per-source failures, etc.) is visible in the CI log.
                detail = json.dumps(data, indent=2, default=str)
                return False, f"Job failed. Full jobStatus payload:\n{detail}"

        except Exception as e:
            print(f"    Error: Status check error (will retry): {e}")

        time.sleep(POLL_INTERVAL_SECONDS)
        elapsed += POLL_INTERVAL_SECONDS

    return False, f"Job {job_id} timed out after {JOB_TIMEOUT_SECONDS}s"
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
    print(f"Config Type ID: {CONFIG_TYPE_ID or '(auto — default profile)'}")
    print(f"Org filter:     {ORG_NAME_FILTER if ORG_NAME_FILTER else '(none)'}")
    print("Status filter:  published only")
    print(f"Verify URLs:    {VERIFY_URLS}")
    print(f"Poll interval:  {POLL_INTERVAL_SECONDS} seconds")
    print(f"Job timeout:    {JOB_TIMEOUT_SECONDS} seconds")
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

    # Batching is intentionally disabled: the CoreModels importer loads the entire
    # model to compare and sync, so splitting the import into batches does not reduce
    # memory usage — and importing schemas in separate batches leaves the model in an
    # invalid state. All schemas are therefore imported in a SINGLE merge job.
    print(f"\nImporting all {len(schemas)} schema(s) in a single merge job...\n")

    # Collect every schema URL (optionally pre-verified) for the single job.
    urls = []
    skipped_keys = []
    for schema in schemas:
        org = schema["organization_name"]
        name = schema["schema_name"]
        url = build_synapse_schema_url(org, name)

        if VERIFY_URLS and not verify_schema_url(url):
            print(f"    ⏭️  Skipping {schema['key']} — URL not accessible: {url}")
            skipped_keys.append(schema["key"])
            continue

        urls.append(url)

    if DRY_RUN:
        print(f"  ⏭️  Dry run — would import {len(urls)} schema(s):")
        for url in urls:
            print(f"       {url}")
        print("\n🔍 Dry run complete — no imports were performed.")
        sys.exit(0)

    if not urls:
        print("No valid schema URLs to import. Exiting.")
        sys.exit(1)

    with requests.Session() as session:
        job_id, reason = queue_merge_job(urls, session)
        if not job_id:
            print(f"  ❌ Failed to queue job: {reason}")
            sys.exit(1)

        print(f"  ✓ Job queued: {job_id}")
        ok, reason = wait_for_job(job_id, session)

    # ──────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"  Total schemas:   {len(schemas)}")
    print(f"  Imported:        {len(urls)}")
    print(f"  ⏭️  Skipped:      {len(skipped_keys)}")

    if skipped_keys:
        print("\nSkipped schemas (URL not accessible):")
        for key in skipped_keys:
            print(f"  - {key}")

    if not ok:
        print(f"\n❌ Import failed: {reason}")
        sys.exit(1)

    print("\n🎉 All published schemas imported successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
