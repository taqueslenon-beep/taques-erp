# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

### Dependency installation
- Install Python dependencies:

```bash
pip install -r requirements.txt
```

### Run the application
- Development server with auto-reload (preferred for UI work):

```bash
python3 iniciar.py
# or (equivalent, skips the wrapper)
python3 dev_server.py
```

- NiceGUI server directly (no file-watching auto-reload):

```bash
python3 -m mini_erp.main
```

- Alternative shell helpers (do the same thing as above, but are less flexible inside Warp):

```bash
./run          # starts mini_erp.main and opens the browser
./start        # starts mini_erp.main without helpers
./start.command  # macOS double‑click entrypoint; calls python3 iniciar.py
```

- Port control (used by `mini_erp/main.py` and `iniciar.py`):
  - Default port comes from `APP_PORT` (falls back to 8080).
  - The startup code will probe 8080 and then a small range of successive ports until it finds a free one.
  - To force a specific port when running `mini_erp.main` directly:

```bash
APP_PORT=9000 python3 -m mini_erp.main
```

### Tests
- Run the full test suite (pytest is listed in `requirements.txt` and the existing tests are under `tests/`):

```bash
pytest
```

- Run a single test module:

```bash
pytest tests/test_diagnose_third_party_monitoring_duplicates.py
```

- Run a single test function (useful when iterating on duplicate‑monitoring logic):

```bash
pytest tests/test_diagnose_third_party_monitoring_duplicates.py::test_main_with_duplicates
```

### Key maintenance / data‑quality scripts
These scripts all live under `scripts/` and use the shared Firebase configuration in `mini_erp/firebase_config.py`.

- Case duplicate diagnosis & cleanup (cases collection):

```bash
# Diagnose duplicates (no writes)
python3 scripts/diagnose_duplicates.py

# Simulate fixes without writing to Firestore
python3 scripts/diagnose_duplicates.py --fix --dry-run

# Apply fixes to Firestore (after reviewing dry‑run output)
python3 scripts/diagnose_duplicates.py --fix --no-dry-run
```

- Process‐level deduplication (processes collection; uses soft delete and creates backups under `backups/`):

```bash
python3 scripts/deduplicacao_processos.py
```

- Third‑party monitoring diagnostics (collection `third_party_monitoring`, exercised by the existing pytest module):

```bash
python3 scripts/diagnose_third_party_monitoring_duplicates.py
```

### Environment / integrations
- Slack integration uses a `.env` file at the repo root. To start from the example:

```bash
cp env.example .env
# Then edit .env and fill SLACK_* and BASE_URL based on SLACK_INTEGRATION.md
```

- Firebase Admin SDK credentials are loaded either from environment variables (`FIREBASE_PRIVATE_KEY_ID`, `FIREBASE_PRIVATE_KEY`, etc.) or from `firebase-credentials.json` at the repo root (see `mini_erp/firebase_config.py`).


## Architecture overview

### High‑level stack
- **Frontend / UI**: [NiceGUI](https://nicegui.io) (Python‑first UI framework) renders HTML/JS via WebSocket; all pages and components are defined in Python.
- **Backend runtime**: Python 3.9+ with NiceGUI’s built‑in Uvicorn/FastAPI stack.
- **Data store**: Google Firebase Firestore (primary NoSQL database) plus Firebase Storage for file uploads.
- **Auth**: Firebase Auth (REST API) plus NiceGUI’s `app.storage.user` for session state.
- **Async / infra**:
  - `watchfiles` provides filesystem watching and process restart in `dev_server.py`.
  - `firebase-admin` is the primary Firestore / Storage / admin client.
- **Auxiliary libraries**: `reportlab` (PDF generation), `Pillow` (avatar/image processing), `slack-sdk` and `python-dotenv` (Slack integration), `requests` (HTTP client for Firebase Auth and Slack‑related flows).

Key high‑level documentation for this stack is in `STACK_TECNOLOGICO.md` and `DEPENDENCIAS.md`; those files are the authoritative reference for technology choices and how modules are organized across `mini_erp/pages/`.

### Server entrypoints and dev workflow
- **`mini_erp/main.py`**
  - Sets up a compatibility shim around `importlib.metadata.packages_distributions` for Python 3.9 so Firebase/Google libraries work even though they expect the new API.
  - Imports NiceGUI (`from nicegui import ui`) and then either imports `mini_erp.pages` as a package or via an explicit `sys.path` tweak, so that all routes under `mini_erp/pages/` are registered on import.
  - Implements `start_server_safe()` which:
    - Chooses a port starting from `APP_PORT` (default 8080), probing and then binding to the first free port in a small range.
    - Differentiates dev mode vs direct mode via `DEV_SERVER=true` (set by `dev_server.py`) to control whether NiceGUI auto‑opens the browser.
    - Calls `ui.run(...)` with explicit configuration for host, WebSocket tuning, and session storage secret.

- **`dev_server.py`**
  - Wraps `mini_erp/main.py` with `watchfiles.run_process`, watching `*.py` files under the project while ignoring common noise directories and extensions.
  - Applies a `StableFilter` that:
    - Only reacts to real `.py` changes within the project tree (ignores `dev_server.py`, `iniciar.py`, backups, virtualenvs, etc.).
    - Debounces restarts to avoid cascades during massive refactors.
  - Sets `DEV_SERVER=true` and `APP_PORT=8080` in the child environment and optionally opens the browser once the app is up.

- **`iniciar.py`**
  - Friendly wrapper that:
    - Scans from port 8080 upwards for a free port.
    - Sets `APP_PORT` to that value.
    - Prefers running `dev_server.py` when present (auto‑reload dev mode) and falls back to `python -m mini_erp.main` when it is not.
  - Also launches a background thread that opens the browser at the chosen URL.

- **Shell helpers (`run`, `start`, `start.command`)**
  - Small bash wrappers that either call `python3 -m mini_erp.main` directly or delegate to `iniciar.py`, used mainly outside of Warp.

### Data access, caching and Firestore conventions
- **Core data access lives in `mini_erp/core.py`** and should generally be preferred over ad‑hoc Firestore code in pages or scripts:
  - A thread‑safe in‑memory cache (`_cache`, `_cache_timestamp`, `_cache_lock`) backs `_get_collection(collection_name)` with a 5‑minute TTL to reduce Firestore reads.
  - Convenience getters like `get_cases_list`, `get_processes_list`, `get_clients_list`, `get_opposing_parties_list`, etc. all delegate to `_get_collection` and benefit from the cache.
  - The cache is explicitly invalidated by helpers around writes (`_save_to_collection`, `_update_in_collection`, `_delete_from_collection`, and `invalidate_cache`).
  - Process records implement **soft delete** via an `isDeleted` flag; `_get_collection('processes')`, `get_child_processes`, and `get_processes_paged` all filter out documents where `isDeleted == True` so UI code does not need to re‑implement that logic.

- **Case–process relationship as a first‑class concern** (see lower half of `mini_erp/core.py` and `DUPLICATE_DIAGNOSIS.md`):
  - **Source of truth** is on **process documents**:
    - `case_ids`: array of case slugs the process belongs to.
    - `cases`: array of case titles (kept for backwards compatibility and display).
  - **Derived data** lives on **case documents**:
    - `process_ids`: array of process `_id`s linked to the case.
    - `processes`: array of process titles for display/backwards compatibility.
  - `sync_processes_cases()` walks both collections, rebuilds these arrays bidirectionally, and **only writes back cases or processes whose derived fields actually changed** (to avoid unnecessary Firestore writes and historical duplication issues).
  - Integrity helpers like `validate_case_process_integrity()` compute and log inconsistencies such as orphaned references or missing `case_ids`.

- **People and documents**:
  - `normalize_client_documents`, `normalize_entity_type_value`, and related helpers in `core.py` standardize CPF/CNPJ fields, client type labels, and display document strings across both the `clients` and `opposing_parties` collections.
  - `get_all_people_for_opposing_parties()` unifies clients and opposing parties into a single list of selectable people for UI components, with consistent `display_name` and type labels.
  - Several helpers (`get_display_name_by_id`, `get_display_name`, `get_full_name`, `format_client_option_for_select`, etc.) implement a consistent naming strategy and are backed by their own short‑lived cache to keep dropdown rendering efficient.

- **Global list compatibility layer**:
  - The bottom of `core.py` exposes an older “global list” API via `_FirestoreList`, `_ListWrapper`, and `_DataDict` so legacy code that expects `cases_list`, `processes_list`, or `data['cases']` continues to work while still going through the cached Firestore accessors.

### Authentication and sessions
- **`mini_erp/auth.py`** encapsulates user authentication and session handling:
  - Uses Firebase Auth’s REST API (`identitytoolkit.googleapis.com`) to authenticate via email/password and returns a small user dict with `uid`, `email`, `idToken`, and `refreshToken`.
  - Persists the current user in `app.storage.user['user']` and exposes `get_current_user()`, `is_authenticated()`, and `logout_user()` helpers around that storage.
  - Provides a `@require_auth` decorator that pages can use to guard routes and redirect unauthenticated users to `/login`.
  - Includes NiceGUI/JS helpers (`logout_e_reiniciar`, `fazer_logout_com_notificacao`) that clear `localStorage`, `sessionStorage`, and cookies on the client, then force a reload to the login page.

- **Session storage secret** is configured via `storage_secret='taques-erp-secret-key-2024'` inside `ui.run(...)` in `mini_erp/main.py`; this is the core knob that ties browser sessions to server‑side storage and should be kept consistent across environments.

### UI modules and page structure
- The UI is organized under `mini_erp/pages/` by **business domain**, with a consistent internal module layout per domain. `DEPENDENCIAS.md` is the best index of what exists.

- Typical domain package structure (`mini_erp/pages/casos/`, `processos/`, `pessoas/`, `painel/`, `governanca/`, etc.):
  - `models.py`: dataclasses / typed dicts for Firestore documents and view models.
  - `database.py`: Firestore operations for that module, usually calling into `mini_erp.core` and `mini_erp.firebase_config` rather than using `firebase_admin` directly.
  - `business_logic.py`: domain‑specific operations (rules, aggregations, transformations) that sit between Firestore and the UI.
  - `ui_components.py` (and sometimes `ui_tables.py`, `ui_dialogs.py`): NiceGUI components composed from primitives (`ui.card`, `ui.row`, `ui.table`, etc.), often wired to the above logic.
  - `<feature>_page.py` or `main.py`: the actual NiceGUI page entrypoint that registers routes and composes the module components.

- **Casos (cases)**
  - Lives under `mini_erp/pages/casos/` and is heavily documented by `GUIA_DEDUPLICACAO.md`, `DUPLICATE_DIAGNOSIS.md`, `DUPLICATE_FIX_SUMMARY.md`, and related files.
  - Implements advanced duplicate detection and cleanup logic in `duplicate_detection.py` and exposes both CLI scripts and admin UI under `/casos/admin/duplicatas` to manage problematic case records.

- **Processos (processes)**
  - Lives under `mini_erp/pages/processos/`.
  - Uses the `isDeleted` soft‑delete convention for processes and coordinates closely with the deduplication script `scripts/deduplicacao_processos.py`.
  - Provides helpers in its `database.py` to create and manage “third‑party monitoring” records, which show up both in the processes module and in the main dashboard.

- **Pessoas (people)**, **Painel (dashboard)**, and **Governança**
  - Follow the same models/database/logic/UI structure and primarily orchestrate views over the same Firestore collections (`clients`, `opposing_parties`, `cases`, `processes`, etc.), leveraging the shared helpers in `core.py` and styling constants in `mini_erp/constants.py`.

### Styling and visual consistency
- Visual styling is predominantly done via Tailwind‑style utility classes attached through NiceGUI’s `.classes(...)` API; `PADROES_ESTILO_NICEGUI.md` summarizes the most common patterns and is worth skimming before making UI changes.
  - Inputs and controls typically use `w-full mb-2` for layout.
  - Cards use combinations like `w-full p-4 mb-4 bg-gray-50` or `w-full p-6 bg-white rounded shadow-sm`.
  - Buttons use semantic colors such as `bg-primary text-white` for primary actions and `bg-red-600 text-white` for destructive ones.

- All **area‑of‑law colors and many other categorical palettes are centralized in `mini_erp/constants.py`**, as described in `CORES_PADRONIZADAS.md`:
  - `AREA_COLORS_BACKGROUND`, `AREA_COLORS_TEXT`, `AREA_COLORS_BORDER`, and `AREA_COLORS_CHART` define a single source of truth for how each legal area (Administrativo, Criminal, Cível/Civil, Tributário, Técnico/projetos, Outros) is rendered in tables and charts.
  - The dashboard (`mini_erp/pages/painel/models.py` and `tab_visualizations.py`) and the processes UI components (`mini_erp/pages/processos/ui_components.py`) both import from these constants so color tweaks only need to be made in one place.
  - Additional maps in `constants.py` (`STATUS_COLORS`, `PROBABILITY_COLORS`, `CASE_TYPE_COLORS`, `CATEGORY_COLORS`, `RESULT_COLORS`, etc.) keep outcome and status visualizations consistent across modules and charts.

When adding or changing any visual representation of areas, statuses, or categories, prefer editing `mini_erp/constants.py` and then wiring the new keys into the relevant page modules rather than hard‑coding colors or labels.

### Slack integration architecture
- The Slack integration is fully described in `SLACK_INTEGRATION.md` and lives in `mini_erp/pages/casos/slack_integration/` with a clear sub‑module split:
  - `slack_config.py`: loads OAuth configuration and tokens (from environment / Firestore) and builds the necessary URLs.
  - `slack_api.py`: wraps the Slack Web API client (`slack-sdk`) for channel enumeration and message fetching, including rate‑limit handling and short‑term caching.
  - `slack_models.py`: data models for messages, channels, and users.
  - `slack_database.py`: Firestore persistence for tokens, channel bindings to cases, message caches, and audit logs.
  - `slack_events.py`: HTTP handlers for Slack Event Subscriptions webhooks, including HMAC SHA256 signature validation using `SLACK_SIGNING_SECRET`.
  - `slack_ui.py` and `slack_settings_page.py`: NiceGUI components and a settings page under `/casos/slack/settings` that let users connect Slack, bind channels to cases, and explore messages inside the case‑detail view.

- OAuth2 flow details and security measures (state/CSRF protection, rate limiting, token encryption design, webhook validation) are diagrammed in `mini_erp/pages/casos/slack_integration/oauth_flow_diagram.md` and operationalized in `setup_guide.md` and `SLACK_INTEGRATION.md`.

- Environment and configuration linkage:
  - `.env` → `env.example` documents `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_SIGNING_SECRET`, `BASE_URL`, and `SLACK_ENCRYPTION_KEY` (planned encryption of stored tokens).
  - Slack webhooks expect URLs rooted at `BASE_URL` such as `/casos/slack/oauth/callback` and `/casos/slack/webhook`; the NiceGUI server must be reachable at those paths for the integration to function.

When modifying Slack‑related code, keep the Firestore schema in `slack_database.py` and the expectations from `SLACK_INTEGRATION.md` and `setup_guide.md` aligned; those documents are the contract between the web UI, background webhooks, and Slack’s API.

### Deduplication and data‑quality tooling
- There is a rich set of documentation and scripts around **deduplicating cases and processes**, as captured in `GUIA_DEDUPLICACAO.md`, `DUPLICATE_DIAGNOSIS.md`, `DUPLICATE_FIX_SUMMARY.md`, and `DUPLICATE_CRITICAL_FINDINGS.md`.

- **Key moving parts:**
  - `mini_erp/pages/casos/duplicate_detection.py`: core logic for detecting and resolving duplicate case records, including merge rules and logging.
  - `sync_processes_cases()` and `validate_case_process_integrity()` in `mini_erp/core.py`: keep case–process links consistent and verify referential integrity.
  - `scripts/diagnose_duplicates.py` and `scripts/diagnose_duplicates_standalone.py`: CLI entrypoints for diagnosing and optionally fixing duplicates, with explicit `--fix`, `--dry-run`, and `--no-dry-run` flags.
  - `scripts/deduplicacao_processos.py`: performs deduplication in the `processes` collection and relies on **soft delete** (`isDeleted`, `deletedAt`, `deletedReason`, `originalProcessId`) plus automatic JSON/markdown backups under `backups/` for safe rollback.

- The documentation emphasizes a workflow of:
  1. Run diagnostic scripts (no writes) and review output.
  2. Run in dry‑run mode with `--fix --dry-run` to see planned changes.
  3. Take a Firestore backup (or rely on the script’s own backups in `backups/`).
  4. Apply real fixes with `--fix --no-dry-run`.

Future code that touches case/process creation or renumbering should consult these docs and reuse the existing helpers to avoid re‑introducing large‑scale duplication problems.

### Third‑party monitoring (acompanhamento de terceiros)
- The **third‑party monitoring** feature is an extension of the processes module and is documented in `TESTES_ACOMPANHAMENTO_TERCEIROS.md`:
  - Firestore collection `third_party_monitoring` stores monitoring records for external proceedings.
  - `mini_erp/pages/processos/database.py` exposes helpers such as `criar_acompanhamento`, `contar_acompanhamentos_ativos`, and retrieval/deletion functions used both by the UI and by manual/automated tests.
  - The main dashboard (`mini_erp/pages/painel/tab_visualizations.py`) surfaces an “Acompanhamentos de Terceiros” card, whose count is driven by these helpers.
  - `tests/test_diagnose_third_party_monitoring_duplicates.py` validates the behavior of `scripts/diagnose_third_party_monitoring_duplicates.py`, asserting on summary statistics and duplicate‑group reporting.

When evolving this feature, keep the contract between the processes UI, dashboard card, scripts, and tests aligned; `TESTES_ACOMPANHAMENTO_TERCEIROS.md` describes the expected user‑visible behavior and how counts should react to changes in the Firestore collection.

### Backups and system restart
- Firestore and Storage backups, as well as system‑restart logs, are stored under `backups/` and documented in `backups/README.md`:
  - Files such as `backup_completo_*.json`, `backup_processes_*.json`, and `deduplication_report_*.md` are created by maintenance scripts (including deduplication and restart tooling).
  - Logs like `reinicializacao_*.log` capture details of system restarts.
  - Manual cleanup for old backups is done with `find` commands that delete JSON/TXT/MD/LOG files older than a retention window.

- Scripts like `scripts/reinicializar_sistema.py` (see the dedicated markdown docs in the repo for details) orchestrate safe restart flows and backup generation; new maintenance tooling should follow the same pattern of writing into `backups/` with timestamped filenames and human‑readable reports.
