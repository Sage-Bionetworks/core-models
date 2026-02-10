"""
import_to_coremodels.py

Reads docs/data.json, fetches each unique schema from the Synapse registry,
and imports it into CoreModels via the Merge JSON Schema API.

Required environment variables:
  COREMODELS_API_URL        - Base URL for CoreModels API (e.g. https://api.coremodels.io)
  COREMODELS_API_TOKEN      - Bearer token for CoreModels
  COREMODELS_PROJECT_ID     - CoreModels project ID
  COREMODELS_SPACE_ID       - Target space ID to import into
  COREMODELS_CONFIG_TYPE_ID - JSON Schema import profile ID

Optional:
  OVERRIDE_NEW_PROPERTIES   - "true" to skip unmapped properties warning (default: "true")
  OVERRIDE_DIFFERENT_SOURCE - "true" to skip different source warning (default: "true")
  OVERRIDE_OVERWRITE        - "true" to skip overwrite warning (default: "true")
  ONLY_ADD_AND_UPDATE       - "true" to only add/update, never remove (default: "true")
  DRY_RUN                   - "true" to only list schemas without importing (default: "false")
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

# Override flags — default to true so imports don't fail on warnings
OVERRIDE_NEW_PROPS = os.environ.get("OVERRIDE_NEW_PROPERTIES", "true").lower() == "true"
OVERRIDE_DIFF_SRC = os.environ.get("OVERRIDE_DIFFERENT_SOURCE", "true").lower() == "true"
OVERRIDE_OVERWRITE = os.environ.get("OVERRIDE_OVERWRITE", "true").lower() == "true"
ONLY_ADD_UPDATE = os.environ.get("ONLY_ADD_AND_UPDATE", "true").lower() == "true"
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

# Synapse schema registry base URL
SYNAPSE_SCHEMA_BASE = "https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered"

# Path to data.json (relative to repo root)
DATA_JSON_PATH = os.environ.get("DATA_JSON_PATH", "docs/data.json")

# Rate limiting: seconds to wait between API calls
RATE_LIMIT_SECONDS = float(os.environ.get("RATE_LIMIT_SECONDS", "1.0"))


def validate_config():
    """Validate that all required env vars are set."""
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
    """Load and parse docs/data.json."""
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run export_orgs.py first.")
        sys.exit(1)

    with open(path, "r") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} total schema version rows from {path}")
    return data


def get_unique_schemas(data):
    """
    Extract unique (organization_name, schema_name) pairs.
    Each pair maps to one schema URL in the Synapse registry.
    We deduplicate because data.json has one row per VERSION,
    but we only need to import each schema once (latest version).
    """
    seen = set()
    unique = []

    for row in data:
        org = row.get("organization_name", "")
        schema = row.get("schema_name", "")
        key = f"{org}-{schema}"

        if key not in seen and org and schema:
            seen.add(key)
            unique.append({
                "organization_name": org,
                "schema_name": schema,
                "key": key,
            })

    print(f"Found {len(unique)} unique schemas to import")
    return unique


def build_synapse_schema_url(org_name, schema_name):
    """Build the Synapse registry URL for a schema."""
    return f"{SYNAPSE_SCHEMA_BASE}/{org_name}-{schema_name}"


def verify_schema_url(url):
    """
    Verify the schema URL is accessible before sending to CoreModels.
    Returns True if the URL returns valid JSON.
    """
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            resp.json()  # Verify it's valid JSON
            return True
        else:
            print(f"  WARNING: Schema URL returned HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"  WARNING: Could not verify schema URL: {e}")
        return False


def import_schema_to_coremodels(schema_url, schema_key):
    """
    Import a single schema into CoreModels using the Merge JSON Schema API.
    Uses FileUrl to point to the Synapse registry URL.
    """
    endpoint = f"{API_URL}/v1/{PROJECT_ID}/mergeJsonSchema"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    params = {
        "SpaceId": SPACE_ID,
        "ConfigTypeId": CONFIG_TYPE_ID,
        "OverrideNewPropertiesWarning": str(OVERRIDE_NEW_PROPS).lower(),
        "OverrideDifferentSourceWarning": str(OVERRIDE_DIFF_SRC).lower(),
        "OverrideOverwriteWarning": str(OVERRIDE_OVERWRITE).lower(),
        "OnlyAddAndUpdate": str(ONLY_ADD_UPDATE).lower(),
    }

    # SourceDtos with the FileUrl pointing to the Synapse schema registry
    body = {
        "SourceDtos": [
            {
                "FileUrl": schema_url
            }
        ]
    }

    try:
        resp = requests.post(
            endpoint,
            headers=headers,
            params=params,
            json=body,
            timeout=120,
        )

        if resp.status_code == 200:
            result = resp.json()
            if result.get("success"):
                print(f"  ✅ Successfully imported: {schema_key}")
                return True
            else:
                error = result.get("error", {})
                msg = error.get("message", "Unknown error")
                fatal = error.get("isFatal", False)
                print(f"  ❌ Import failed: {msg} (fatal={fatal})")
                return False
        else:
            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print(f"  ❌ Request timed out for {schema_key}")
        return False
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False


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
    print(f"Override flags: new_props={OVERRIDE_NEW_PROPS}, "
          f"diff_src={OVERRIDE_DIFF_SRC}, overwrite={OVERRIDE_OVERWRITE}, "
          f"add_update_only={ONLY_ADD_UPDATE}")
    print()

    # Load data
    data = load_data_json(DATA_JSON_PATH)
    schemas = get_unique_schemas(data)

    if not schemas:
        print("No schemas found to import. Exiting.")
        sys.exit(0)

    # Track results
    success_count = 0
    fail_count = 0
    skip_count = 0
    failed_schemas = []

    for i, schema in enumerate(schemas, start=1):
        org = schema["organization_name"]
        name = schema["schema_name"]
        key = schema["key"]
        url = build_synapse_schema_url(org, name)

        print(f"\n[{i}/{len(schemas)}] {key}")
        print(f"  URL: {url}")

        if DRY_RUN:
            print("  ⏭️  Skipped (dry run)")
            skip_count += 1
            continue

        # Verify the schema URL is accessible
        if not verify_schema_url(url):
            print(f"  ⏭️  Skipping — URL not accessible")
            skip_count += 1
            failed_schemas.append({"key": key, "reason": "URL not accessible"})
            continue

        # Import to CoreModels
        ok = import_schema_to_coremodels(url, key)
        if ok:
            success_count += 1
        else:
            fail_count += 1
            failed_schemas.append({"key": key, "reason": "Import failed"})

        # Rate limiting
        if i < len(schemas):
            time.sleep(RATE_LIMIT_SECONDS)

    # ──────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"  Total schemas:  {len(schemas)}")
    print(f"  ✅ Succeeded:   {success_count}")
    print(f"  ❌ Failed:      {fail_count}")
    print(f"  ⏭️  Skipped:    {skip_count}")

    if failed_schemas:
        print("\nFailed/skipped schemas:")
        for f in failed_schemas:
            print(f"  - {f['key']}: {f['reason']}")

    # Exit with error code if any failures
    if fail_count > 0:
        print(f"\n⚠️  {fail_count} schema(s) failed to import.")
        sys.exit(1)
    else:
        print("\n🎉 All schemas processed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()