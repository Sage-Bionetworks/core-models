# Contributing & Maintenance Guide

This guide is for people who **maintain** the Index of Data Models — the data pipeline, the
GitHub Actions workflows, and the site itself. If you just want to browse or use the schemas,
start with the [README](README.md) and the [live site](https://sage-bionetworks.github.io/core-models/).

---

## Contents

- [How it fits together](#how-it-fits-together)
- [The data pipeline](#the-data-pipeline)
- [GitHub Actions workflows](#github-actions-workflows)
- [Required secrets](#required-secrets)
- [Running the pipeline locally](#running-the-pipeline-locally)
- [Common tasks](#common-tasks)
- [Conventions](#conventions)

---

## How it fits together

There are three moving parts:

1. **A React site** (`src/`, built with Vite) — the browsable UI, deployed to GitHub Pages.
2. **Generated data** (`public/data.json`, `public/staging_checks.json`) — the schema list and
   staging results the site reads at runtime.
3. **A Python pipeline** (`scripts/`) — pulls from Synapse, validates, and publishes to CoreModels.

The site is a static build: at runtime it just fetches the two JSON files from `public/`. All the
"intelligence" (what schemas exist, are they valid) is baked into those files by the pipeline. See
[README → How the data stays up to date](README.md#how-the-data-stays-up-to-date) for the flow
diagram.

---

## The data pipeline

All three scripts live in `scripts/` and are configured entirely through environment variables.

### `scripts/export_orgs.py` → `public/data.json`

Lists every organization and schema in the Synapse JSON Schema registry and writes one row per
schema (its latest version) to `public/data.json`. It caches by SHA-256 so unchanged schemas
skip a redundant detail fetch.

| Env var | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SYNAPSE_AUTH_TOKEN` | ✅ | — | Synapse personal access token |
| `ORG_NAME_FILTER` | | *(all)* | Export only one org (e.g. `ADA.PSI`) |
| `MAX_WORKERS` | | `32` | Concurrent threads |
| `OUTPUT_PATH` | | `public/data.json` | Output file |

The `PUBLISHED_ORGS` set near the top of the script decides which organizations are marked
`published` (vs `draft`). See [Common tasks](#mark-an-organization-as-published).

### `scripts/check_schema_uris_staging.py` → `public/staging_checks.json`

Reads `public/data.json`, and for each published schema verifies its URI resolves in the Synapse
**staging** registry. Optionally creates (and cleans up) a curation task per URI as a deeper check.

| Env var | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SYNAPSE_AUTH_TOKEN` | ✅ | *(or `~/.synapseConfig`)* | Synapse token |
| `DATA_JSON_PATH` | | `public/data.json` | Input list (results are written alongside it) |
| `STATUS_FILTER` | | `published` | `published` or `all` |
| `CHECK_TASK_CREATION` | | `false` | Also attempt task creation |
| `STAGING_FOLDER_ID` | if task creation | — | Staging folder for test tasks |
| `ASSIGNEE_PRINCIPAL_ID` | if task creation | — | User/team to assign test tasks |
| `MAX_WORKERS` | | `8` | Concurrent threads |

### `scripts/import_to_coremodels.py` → CoreModels

Reads `public/data.json` and imports each **published** schema into CoreModels via its Merge JSON
Schema API.

| Env var | Required | Purpose |
| --- | --- | --- |
| `COREMODELS_API_URL` | ✅ | CoreModels API base URL |
| `COREMODELS_API_TOKEN` | ✅ | Bearer token |
| `COREMODELS_PROJECT_ID` | ✅ | Target project |
| `COREMODELS_SPACE_ID` | ✅ | Target space |
| `COREMODELS_CONFIG_TYPE_ID` | | JSON Schema import profile. **Leave empty/unset** to auto-select the default profile (recommended — survives profile-id migrations). CoreModels v3.9.0 changed the default id to `d7cf1119ad8b84b8e3a122e5a64d006e`. |
| `ORG_NAME_FILTER` | | Import only one org |
| `DATA_JSON_PATH` | | Input list (default `public/data.json`) |
| `DRY_RUN` | | `true` to list without importing |

*(Additional tuning vars — `MAX_WORKERS`, `RATE_LIMIT_SECONDS`, `BATCH_SIZE`, override flags — are
documented in the script's docstring.)*

---

## GitHub Actions workflows

### `.github/workflows/update-data.yml` — the daily pipeline

Runs on a **schedule (06:00 UTC daily)**, on **manual dispatch** (with an optional `org_name`
filter), and on **push to `main`**. Jobs:

| Job | What it does | When |
| --- | --- | --- |
| `update-data` | Runs `export_orgs.py`, commits `public/data.json` to a run-scoped branch | if data changed |
| `check-staging` | Runs `check_schema_uris_staging.py`, commits `public/staging_checks.json` to the same branch | always (non-blocking) |
| `open-pr` | Opens one PR for the collected changes | if either file changed |
| `deploy-pages` | Builds the React app and deploys to GitHub Pages | **push to `main` only** |
| `publish-coremodels` | Runs `import_to_coremodels.py` | after deploy |

Because branch protection blocks direct pushes to `main`, automated data changes always arrive as
a reviewable pull request. Merging that PR is what actually updates the public site and CoreModels.

### `.github/workflows/check-staging-synapseclient-develop.yml` — pre-release check

Manual-only. Runs the same staging check against the **`develop`** build of the Synapse Python
client and uploads the results as a workflow artifact. It never commits, deploys, or publishes —
it's an early-warning smoke test for upcoming client releases.

---

## Required secrets

Set these in **Settings → Secrets and variables → Actions**:

| Secret | Used by |
| --- | --- |
| `SYNAPSE_AUTH_TOKEN` | export + staging check |
| `STAGING_FOLDER_ID` | staging check (task creation) |
| `ASSIGNEE_PRINCIPAL_ID` | staging check (task creation) |
| `COREMODELS_API_URL` | CoreModels publish |
| `COREMODELS_API_TOKEN` | CoreModels publish |
| `COREMODELS_PROJECT_ID` | CoreModels publish |
| `COREMODELS_SPACE_ID` | CoreModels publish |
| `COREMODELS_CONFIG_TYPE_ID` | CoreModels publish |

---

## Running the pipeline locally

Create a `.env` file **in the repository root** (it is git-ignored) with the variables above, then
run from the repo root so the default `public/…` paths resolve:

```bash
pip install synapseclient requests python-dotenv

# Regenerate the schema list (tip: scope to one org while testing)
ORG_NAME_FILTER=sage.schemas.dpe python scripts/export_orgs.py

# Validate against staging
python scripts/check_schema_uris_staging.py

# Preview a CoreModels import without writing anything
DRY_RUN=true python scripts/import_to_coremodels.py
```

To avoid overwriting the committed `public/data.json` while experimenting, point the scripts at a
throwaway path with `OUTPUT_PATH` / `DATA_JSON_PATH`.

---

## Common tasks

### Mark an organization as published

Edit the `PUBLISHED_ORGS` set in [`scripts/export_orgs.py`](scripts/export_orgs.py) and add the
organization's exact `organization_name`. Published orgs are the ones shown by default, validated
against staging, and imported into CoreModels.

### Add or edit a DCC link

Edit [`src/data/dcc.js`](src/data/dcc.js) — each entry has `repo`, `schemas`, `docs`, and
`portal` links (use `null` for any that don't exist). Update the `count` in the `TABS` array in
[`src/App.jsx`](src/App.jsx) if you change how many DCCs are listed.

### Change the update schedule

Edit the `cron` expression under `on.schedule` in
[`.github/workflows/update-data.yml`](.github/workflows/update-data.yml).

### Regenerate the data by hand

Trigger **Update Schema Data → Deploy Pages → Publish to CoreModels** from the Actions tab
(`workflow_dispatch`), optionally with an `org_name` filter. It will open a PR with any changes.

---

## Conventions

- **Never hand-edit** `public/data.json` or `public/staging_checks.json` — they're generated.
- **Never commit secrets.** Local credentials go in the git-ignored root `.env`; CI uses GitHub
  Secrets.
- **Keep `public/` for served assets only.** Tooling and one-off scripts belong in `scripts/`, so
  they aren't published to the GitHub Pages site.
- The site's base path is `/core-models/` (`vite.config.js`) because GitHub Pages serves it from a
  subpath. The app fetches data with relative URLs (`./data.json`), so it keeps working under that
  base.
