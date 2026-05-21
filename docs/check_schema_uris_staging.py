"""
check_schema_uris_staging.py

Reads docs/data.json, extracts all published schema URIs, verifies each
one is accessible in the Synapse staging registry, and optionally attempts
to create a curation task for each URI (cleaning up afterward).

Usage:
    python docs/check_schema_uris_staging.py

Optional environment variables:
    SYNAPSE_AUTH_TOKEN      - Synapse personal access token (or uses ~/.synapseConfig)
    DATA_JSON_PATH          - Path to data.json (default: docs/data.json)
    STATUS_FILTER           - Which statuses to check: "published", "all" (default: "published")
    CHECK_TASK_CREATION     - "true" to also attempt task creation for each URI (default: false)
    STAGING_FOLDER_ID       - Synapse folder ID in staging to create test tasks in (required if CHECK_TASK_CREATION=true)
    ASSIGNEE_PRINCIPAL_ID   - Synapse user/team ID to assign test tasks to (required if CHECK_TASK_CREATION=true)
    MAX_WORKERS             - Concurrent threads (default: 8)
"""

import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from synapseclient import Synapse
from synapseclient.extensions.curator import create_file_based_metadata_task

load_dotenv()

logging.getLogger("synapseclient").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

STAGING_REPO = "https://repo-staging.prod.sagebase.org/repo/v1"
STAGING_AUTH = "https://repo-staging.prod.sagebase.org/auth/v1"
STAGING_FILE = "https://repo-staging.prod.sagebase.org/file/v1"

DATA_JSON_PATH = os.environ.get("DATA_JSON_PATH", "docs/data.json")
STATUS_FILTER = os.environ.get("STATUS_FILTER", "published").lower()
CHECK_TASK_CREATION = os.environ.get("CHECK_TASK_CREATION", "true").lower() == "true"
STAGING_FOLDER_ID = os.environ.get("STAGING_FOLDER_ID", "")
ASSIGNEE_PRINCIPAL_ID = os.environ.get("ASSIGNEE_PRINCIPAL_ID", "")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "8"))


def login_staging():
    syn = Synapse(
        repoEndpoint=STAGING_REPO,
        authEndpoint=STAGING_AUTH,
        fileHandleEndpoint=STAGING_FILE,
        silent=True,
    )
    syn.login(authToken=os.environ.get("SYNAPSE_AUTH_TOKEN"), silent=True)
    return syn


def load_unique_uris(path):
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        sys.exit(1)

    with open(path, "r") as f:
        data = json.load(f)

    if STATUS_FILTER != "all":
        data = [r for r in data if (r.get("status") or "").strip().lower() == STATUS_FILTER]

    seen = set()
    uris = []
    for row in data:
        org = row.get("organization_name", "")
        schema = row.get("schema_name", "")
        if org and schema:
            key = f"{org}-{schema}"
            if key not in seen:
                seen.add(key)
                uris.append(key)
    return uris


def check_uri(uri, syn):
    try:
        syn.restGET(f"/schema/type/registered/{uri}")
        return True, None
    except Exception as e:
        return False, str(e)


def create_task(uri, syn):
    entity_view_id = None
    task_id = None
    try:
        entity_view_id, task_id = create_file_based_metadata_task(
            synapse_client=syn,
            folder_id=STAGING_FOLDER_ID,
            curation_task_name=f"DryRun-{uri}",
            instructions="Automated dry run check — safe to delete.",
            attach_wiki=False,
            entity_view_name=uri,
            schema_uri=uri,
            assignee_principal_id=ASSIGNEE_PRINCIPAL_ID,
        )
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        for entity_id in filter(None, [entity_view_id, task_id]):
            try:
                syn.delete(entity_id)
            except Exception:
                pass


def run_check(uri, syn):
    ok, err = check_uri(uri, syn)
    if not ok:
        return uri, False, f"Schema not found: {err}"
    if CHECK_TASK_CREATION:
        ok, err = create_task(uri, syn)
        if not ok:
            return uri, False, f"Task creation failed: {err}"
    return uri, True, None


def main():
    if CHECK_TASK_CREATION:
        missing = [n for n, v in [("STAGING_FOLDER_ID", STAGING_FOLDER_ID), ("ASSIGNEE_PRINCIPAL_ID", ASSIGNEE_PRINCIPAL_ID)] if not v]
        if missing:
            print(f"ERROR: {', '.join(missing)} are required when CHECK_TASK_CREATION=true")
            sys.exit(1)

    syn = login_staging()
    uris = load_unique_uris(DATA_JSON_PATH)

    if not uris:
        print("No schemas found to check.")
        sys.exit(0)

    action = "schema URI + task creation" if CHECK_TASK_CREATION else "schema URI"
    print(f"Checking {len(uris)} schemas ({action})...\n")

    passed = []
    failed = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_check, uri, syn): uri for uri in uris}
        for f in as_completed(futures):
            uri, ok, error = f.result()
            if ok:
                passed.append(uri)
                print(f"  OK    {uri}")
            else:
                failed.append((uri, error))
                print(f"  FAIL  {uri}  —  {error}")

    print(f"\n{len(passed)}/{len(uris)} passed")
    if failed:
        print(f"{len(failed)} failed:")
        for uri, err in sorted(failed):
            print(f"  - {uri}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
