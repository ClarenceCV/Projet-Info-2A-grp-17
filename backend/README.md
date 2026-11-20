# LaborScope — Backend (developer guide)

REST API of LaborScope, built with **FastAPI**. It imports labour market data from the
[ILOSTAT](https://ilostat.ilo.org) API, stores it in PostgreSQL, computes the analyses displayed by the
Streamlit frontend, and manages user accounts, roles and the action journal.

This file is for **developers**. To install and use the application, see the [root README](../README.md).

---

## Tech stack

| Purpose | Tool |
| :--- | :--- |
| Language | Python ≥ 3.12 |
| Web framework / server | FastAPI, Uvicorn |
| Database | PostgreSQL, accessed with **psycopg2** (hand-written SQL in the DAOs, no ORM) |
| Data processing | pandas, requests (ILOSTAT API) |
| Security | bcrypt (password hashing), random session tokens |
| PDF report | fpdf2, matplotlib |
| Dependencies / environment | [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`) |
| Tests / lint | pytest, ruff |

---

## Architecture

The code follows a **layered architecture**: each layer only calls the one below it.

```
  HTTP request (frontend, /docs, curl)
          │
          ▼
  controller/   FastAPI routes: read the request, check access, return JSON or HTTP errors
          │            uses schema/ (Pydantic models: format of requests and responses)
          ▼
  service/      business logic: analyses, rules (password length, roles...), journal
          │            manipulates business_object/ (plain dataclasses: Utilisateur, Indicateur...)
          ▼
  dao/          SQL queries, one DAO per table
          │
          ▼
  PostgreSQL    schema "laborscope"
```

```
backend/
├── pyproject.toml, uv.lock   dependencies (run every `uv` command from backend/)
├── logging_config.yml        logging configuration
├── logs/                     log files (created at startup, not versioned)
└── src/
    ├── main.py               entry point: creates the FastAPI app and registers the routers
    ├── config_import.py      indicators and countries imported from ILOSTAT (the only place to edit)
    ├── business_object/      dataclasses: Indicateur, Pays, Utilisateur, ActionJournal, Selection
    ├── controller/           one router per theme + auth.py (access guards)
    ├── schema/               Pydantic models (inputs / outputs of the API)
    ├── service/              business logic
    ├── dao/                  database access + db_connection.py (single shared connection)
    ├── fetcher/              ILOSTAT import: fetcher (download) → parser (clean) → data_processing (save)
    ├── utils/                reset_database, default accounts, password hashing, logging, singleton
    └── tests/                pytest tests, one folder per layer
```

---

## Database

Scripts are in [`data/`](../data):

- **`init_db.sql`**: drops and recreates the `laborscope` schema with **empty** tables.
- **`pop_db.sql`**: small extract of real ILOSTAT data (3 indicators, 6 countries, since 2023).
  **Fallback only**, when the ILOSTAT API cannot be reached (`reset_database --exemple`).

Labour market data uses a **star schema**:

| Table | Role | Key |
| :--- | :--- | :--- |
| `pays` | dimension: countries / regions | `code_iso` (`FRA`) |
| `indicateur` | dimension: ILOSTAT indicators (label, unit, frequency) | `id`, `code` unique |
| `observation` | fact table: one ILOSTAT value | (`indicateur_id`, `code_iso`, `source`, `periode`, `sexe`, `classif1`) |
| `utilisateur` | accounts: pseudo, bcrypt hash, role, session token | `id`, `pseudo` unique |
| `journal` | action history (who, what, when, detail) | `id` |

The primary key of `observation` is what makes the import **idempotent**: the DAO uses
`INSERT ... ON CONFLICT DO UPDATE`, so running the import again updates values instead of creating duplicates.

---

## Setup and run

All commands below assume the `.env` file exists **at the project root** (copy `.env.example` and fill in
the `POSTGRES_*` values, see the root README).

```bash
cd backend
uv sync                                     # creates backend/.venv with all dependencies (dev tools included)

cd src
uv run python -m utils.reset_database       # empty tables + default accounts   (⚠ deletes all data)
uv run python -m fetcher.charger_donnees    # imports the indicators of config_import.py from ILOSTAT
uv run python main.py                       # starts the API on http://localhost:5000
```

- Interactive documentation: **`/docs`** (the root URL `/` redirects there).
- ILOSTAT unreachable? `uv run python -m utils.reset_database --exemple` also loads `data/pop_db.sql`.
- To follow a new indicator or country: edit `src/config_import.py`, then run the import again.

### Environment variables (`.env` at the project root)

| Variable | Used by | Description | Example |
| :--- | :--- | :--- | :--- |
| `POSTGRES_HOST` | backend | PostgreSQL host | `postgresql-123456` |
| `POSTGRES_PORT` | backend | PostgreSQL port | `5432` |
| `POSTGRES_DATABASE` | backend | database name | `defaultdb` |
| `POSTGRES_USER` | backend | database user | `user-xxxx` |
| `POSTGRES_PASSWORD` | backend | database password | — |
| `POSTGRES_SCHEMA` | backend | schema of the application | `laborscope` |
| `UVICORN_HOST` | backend | listening address (`0.0.0.0` on Onyxia) | `0.0.0.0` |
| `UVICORN_PORT` | backend | API port | `5000` |
| `BACKEND_URL` | frontend | address of this API | `http://localhost:5000` |
| `BACKEND_TIMEOUT` | frontend | request timeout, in seconds | `10` |

---

## Endpoints

Access levels: **public** (no token), **user** (logged in, otherwise `401`), **admin** (`401` if not logged in,
`403` if not admin). Full parameters and examples are in `/docs`.

| Method | Route | Access | Description |
| :--- | :--- | :--- | :--- |
| **Accounts** | | | |
| `POST` | `/login` | public | checks pseudo / password, returns a session token |
| `POST` | `/logout` | user | invalidates the token |
| `POST` | `/utilisateurs` | public | creates an account (role `utilisateur`) |
| `GET` | `/utilisateurs/moi` | user | current user |
| **Reference data** | | | |
| `GET` | `/indicateurs` | public | indicators available |
| `GET` | `/indicateurs/{code}` | public | one indicator (`404` if unknown) |
| `GET` | `/indicateurs/{code}/classif1` | public | breakdowns available (professions or age groups) |
| `GET` | `/pays` | public | countries available |
| `GET` | `/observations` | public | raw observations, with filters (country, period, sex, classif1) |
| **Analyses** | | | |
| `GET` | `/analyses/evolution` | public | time series of an indicator for one or several countries (F3) |
| `GET` | `/analyses/comparaison-pays` | public | ranking of countries on the latest common period (F4) |
| `POST` | `/analyses/multi-indicateurs` | public | 1 to 4 series compared, optionally in base 100 (F5) |
| `GET` | `/rapport` | public | generates a PDF report (FO3) |
| **Administration** | | | |
| `GET` / `POST` | `/admin/utilisateurs` | admin | lists accounts / creates an account with any role |
| `DELETE` | `/admin/utilisateurs/{id}` | admin | deletes an account (not one's own) |
| `GET` | `/admin/journal` | admin | action history, filters `action`, `pseudo`, `limite` |
| `POST` | `/admin/import` | admin | runs the full ILOSTAT import (several minutes) |
| `PUT` / `DELETE` | `/admin/observations` | admin | modifies / deletes one observation (`404` if missing) |
| `GET` | `/admin/logs` | admin | last lines of the technical log file |

---

## Authentication and roles

**Flow**

1. `POST /login` with `{"pseudo": "...", "mot_de_passe": "..."}`. The password is checked against the
   bcrypt hash; on success a random token (`secrets.token_urlsafe(32)`) is stored in `utilisateur.token`
   and returned. Wrong pseudo and wrong password give the **same** `401` message (no account enumeration).
2. The client sends the token in the **`X-Auth-Token`** header of every request
   (in `/docs`: *Authorize* button, top right).
3. `POST /logout` sets the token back to `NULL`: it no longer works.

**Guards** ([`controller/auth.py`](src/controller/auth.py)), executed by FastAPI before the route:

```python
from fastapi import Depends
from controller.auth import admin_requis, utilisateur_connecte

@router.get("/something")
def my_route(utilisateur: Utilisateur = Depends(utilisateur_connecte)):  # logged in, else 401
    ...

@router.delete("/something")
def my_admin_route(admin: Utilisateur = Depends(admin_requis)):        # admin, else 401 / 403
    ...
```

**Rules and security choices**

- Two roles: `utilisateur` and `admin`. Self-registration always creates a `utilisateur`;
  only an admin can create another admin. An admin cannot delete their own account.
- Pseudo: 1 to 30 characters. Password: at least 8 characters, at most 72 bytes (bcrypt limit).
- Passwords are **never** stored or returned: only the bcrypt hash is saved, and response models
  (`schema/utilisateur_model.py`) contain no password field.
- Default accounts, recreated by every reset: `user / user` and `admin / admin`
  ([`utils/comptes_par_defaut.py`](src/utils/comptes_par_defaut.py)). They are deliberately simple for the
  demo and must be removed or changed for a real deployment.
- Sensitive parameters (`password`, `token`, `secret`...) are masked as `*****` in the logs by the `@log` decorator.

---

## Action journal

Every significant action is saved in the `journal` table and visible on the admin page *Logs et historique*.

| Keyword | Action |
| :--- | :--- |
| `connexion`, `echec_connexion`, `deconnexion` | login, failed login, logout |
| `creation_compte`, `suppression_compte` | account created / deleted |
| `import_donnees` | ILOSTAT import (number of observations saved) |
| `modification_donnee`, `suppression_donnee` | observation modified / deleted (key and new value) |

Two rules (see [`service/journal_service.py`](src/service/journal_service.py)):

- an action is journaled **only after it succeeded** (a `404` writes nothing);
- the journal **never makes an action fail**: if writing to it fails, the action is still returned as successful.

The pseudo is copied into each line, so the history stays readable after an account is deleted.

To journal a new action: add its keyword to `ACTIONS` in
[`business_object/action_journal.py`](src/business_object/action_journal.py), then call
`JournalService().enregistrer(utilisateur, "keyword", "detail")`.

---

## Adding an endpoint, step by step

Example: a route returning the number of observations of an indicator.

1. **DAO** (`dao/observation_dao.py`): add a method with the SQL query (always with `%(name)s` parameters,
   never string formatting, to avoid SQL injection).
2. **Service** (`service/observation_service.py`): call the DAO, apply business rules, return a business object
   or a DataFrame.
3. **Schema** (`schema/`): if the response is a new shape, describe it with a Pydantic model.
4. **Controller** (`controller/observation_controller.py`): add the route with `response_model=...`,
   a docstring (shown in `/docs`), `Depends(...)` for access, and `HTTPException(404, ...)` for missing data.
   A new controller must also be registered in `main.py` with `app.include_router(...)`.
5. **Tests**: one test for the service (DAO mocked) and one for the route (`TestClient`, service mocked).

---

## Tests

```bash
cd backend
uv run pytest                          # all tests (configuration in pyproject.toml)
uv run pytest src/tests/test_service   # one folder
```

| Folder | What is tested | Database |
| :--- | :--- | :--- |
| `test_business_object/` | dataclasses and their validation | no |
| `test_service/` | business logic, DAOs replaced by mocks | no |
| `test_controller/` | routes, HTTP codes, `401` / `403` guards, with FastAPI's `TestClient` | no |
| `test_fetcher/` | ILOSTAT download, parsing, retry on network errors (HTTP mocked) | no |
| `test_dao/` | real SQL queries | **yes** |

DAO tests run against the database of the `.env` and only use recognisable test data (country `ZZZ`,
indicator `TEST_DAO`, pseudos starting with `test_dao`), deleted before and after each test.
When the database is unreachable, they are **skipped** with the reason displayed, so the rest of the
suite can still run anywhere.

---

## Logging

- Configured by [`logging_config.yml`](logging_config.yml), initialised in `main.py`.
- Output: the console (`INFO` and above) and `backend/logs/laborscope.log` (`DEBUG` and above, rotation at 10 MB,
  5 backups).
- The `@log` decorator ([`utils/log_utils.py`](src/utils/log_utils.py)) writes the start, end, result summary
  and errors of a method, indented by call depth.
- Admins can read the last lines in the frontend (*Logs et historique → Logs techniques*), through `GET /admin/logs`.

---

## Code quality

```bash
cd backend
uv run pylint src              # code quality score (target: 10/10), configured in pyproject.toml
uv run ruff check src          # lint (style, imports, common bugs)
uv run ruff check src --fix    # automatic fixes
```

The same `uv run pylint src` command works in `frontend/`. Maximum line length: 100 characters.
Every module, class and public function has a docstring (test functions excepted: their name
describes the tested case).

Conventions: code and docstrings in French (domain vocabulary), docstrings with `Args:` / `Returns:` /
`Raises:` sections, no business logic in controllers, no SQL outside DAOs.
