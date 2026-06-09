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
from datetime import datetime, timezone, date

import requests
from dotenv import load_dotenv
from synapseclient import Folder, Synapse
from synapseclient.extensions.curator import create_file_based_metadata_task

load_dotenv()

logging.getLogger("synapseclient").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

STAGING_REPO = "https://repo-staging.prod.sagebase.org/repo/v1"
STAGING_AUTH = "https://repo-staging.prod.sagebase.org/auth/v1"
STAGING_FILE = "https://repo-staging.prod.sagebase.org/file/v1"

DATA_JSON_PATH = os.environ.get("DATA_JSON_PATH", "docs/data.json")
_data_dir = os.path.dirname(DATA_JSON_PATH) or "."
CHECKS_JSON_PATH = os.path.join(_data_dir, "staging_checks.json")
STATUS_FILTER = os.environ.get("STATUS_FILTER", "published").lower()
CHECK_TASK_CREATION = os.environ.get("CHECK_TASK_CREATION", "true").lower() == "true"
STAGING_FOLDER_ID = os.environ.get("STAGING_FOLDER_ID", "")
ASSIGNEE_PRINCIPAL_ID = os.environ.get("ASSIGNEE_PRINCIPAL_ID", "")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "8"))


def staging_is_available(timeout: int = 10) -> bool:
    """
    Probe the staging /status endpoint.
    Returns False (skip) when:
      - status field is not "READ_WRITE"  (e.g. "READ_ONLY" during migration)
      - HTTP 502 / 503
      - Connection error or timeout
    """
    probe_url = f"{STAGING_REPO}/status"
    try:
        r = requests.get(probe_url, timeout=timeout)
        if r.status_code in (502, 503):
            print(f"Staging returned HTTP {r.status_code} — skipping checks.")
            return False
        data = r.json()
        status = data.get("status", "").upper()
        if status != "READ_WRITE":
            msg = data.get("currentMessage", "")
            print(f"Staging is {status}{f' — {msg}' if msg else ''}. Write services unavailable, skipping checks.")
            return False
        return True
    except requests.exceptions.Timeout:
        print(f"Staging probe timed out after {timeout}s — skipping checks.")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"Staging unreachable ({e}) — skipping checks.")
        return False


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


def clear_trash(syn):
    try:
        # Collect all entity IDs across paginated results
        entity_ids = []
        next_page_token = None
        while True:
            url = "/trashcan/view"
            if next_page_token:
                url += f"?nextPageToken={next_page_token}"
            response = syn.restGET(url)
            results = response.get("results", [])
            entity_ids.extend(r["entityId"] for r in results)
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        if not entity_ids:
            print("Staging trash is empty.")
            return

        print(f"Found {len(entity_ids)} item(s) in staging trash — purging...")
        for entity_id in entity_ids:
            try:
                syn.restPUT(f"/trashcan/purge/{entity_id}")
            except Exception as e:
                print(f"  WARNING: Could not purge {entity_id}: {e}")
        print(f"Staging trash cleared.\n")

    except Exception as e:
        print(f"WARNING: Could not clear staging trash: {e}\n")


def check_uri(uri, syn):
    try:
        syn.restGET(f"/schema/type/registered/{uri}")
        return True, None
    except Exception as e:
        return False, str(e)


def create_task(uri, syn):
    try:
        run_date = date.today().isoformat()  # e.g. 2026-05-27
        folder = syn.store(Folder(name=f"{uri}-{run_date}", parent=STAGING_FOLDER_ID))
        create_file_based_metadata_task(
            synapse_client=syn,
            folder_id=folder.id,
            curation_task_name=f"DryRun-{uri}-{run_date}",
            instructions="Automated dry run check.",
            attach_wiki=False,
            entity_view_name=uri,
            schema_uri=uri,
            assignee_principal_id=ASSIGNEE_PRINCIPAL_ID,
        )
        return True, None
    except Exception as e:
        return False, str(e)


def run_check(uri, syn):
    if CHECK_TASK_CREATION:
        # create_file_based_metadata_task will fail with a clear error if the
        # schema doesn't exist, so skip the separate URI check (saves 1 round trip)
        ok, err = create_task(uri, syn)
        if not ok:
            return uri, False, err
    else:
        ok, err = check_uri(uri, syn)
        if not ok:
            return uri, False, f"Schema not found: {err}"
    return uri, True, None


def main():
    # Fast pre-flight: bail out immediately if staging is in maintenance
    if not staging_is_available():
        sys.exit(0)

    if CHECK_TASK_CREATION:
        missing = [n for n, v in [("STAGING_FOLDER_ID", STAGING_FOLDER_ID), ("ASSIGNEE_PRINCIPAL_ID", ASSIGNEE_PRINCIPAL_ID)] if not v]
        if missing:
            print(f"ERROR: {', '.join(missing)} are required when CHECK_TASK_CREATION=true")
            sys.exit(1)

    syn = login_staging()
    clear_trash(syn)
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

    # Write staging_checks.json for the HTML UI
    results = {}
    for uri in passed:
        results[uri] = {"ok": True}
    for uri, err in failed:
        results[uri] = {"ok": False, "error": err}
    checks = {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results": results,
    }
    with open(CHECKS_JSON_PATH, "w") as fh:
        json.dump(checks, fh, indent=2)
    print(f"\nWrote results to {CHECKS_JSON_PATH}")

    print(f"\n{len(passed)}/{len(uris)} passed")
    if failed:
        print(f"{len(failed)} failed:")
        for uri, err in sorted(failed):
            print(f"  - {uri}: {err}")


if __name__ == "__main__":
    main()
