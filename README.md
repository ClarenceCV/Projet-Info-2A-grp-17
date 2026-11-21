# LaborScope — Global labour market analysis

**LaborScope** is a web application to explore and compare labour market indicators across
about 80 countries, using data from the International Labour Organization
([ILOSTAT](https://ilostat.ilo.org)).

It downloads the data from the ILOSTAT API, stores it in a PostgreSQL database, and offers
interactive analyses (time series, country rankings, world map, multi-indicator comparison,
PDF reports) to logged-in users, plus an administration area.

ENSAI 2nd-year IT project — group 17 (2026).

- **Interface**: Streamlit (in French) — **API**: FastAPI — **Database**: PostgreSQL — **Python** ≥ 3.12, managed with [uv](https://docs.astral.sh/uv/)

---

## Table of contents

1. [Features](#features)
2. [Data](#data)
3. [Quick start on Onyxia](#quick-start-on-onyxia)
4. [Accounts and roles](#accounts-and-roles)
5. [Using the application](#using-the-application)
6. [Administration](#administration)
7. [Highlights](#highlights)
8. [Project structure](#project-structure)
9. [Tests and code quality](#tests-and-code-quality)
10. [Troubleshooting](#troubleshooting)
11. [Authors](#authors)

---

## Features

| # | Feature | Where to find it (menu of the interface) |
|---|---|---|
| **F1** | Download indicators from the ILOSTAT API | command line (step 5 below) or *Administration → Données* |
| **F2** | Clean and store the data in PostgreSQL (no duplicates when re-imported) | automatic, during the import |
| **F3** | Evolution of an indicator over the last *n* quarters, for one or several countries | *Analyses → Évolution (F3)* |
| **F4** | Compare countries on an indicator: full ranking, highest and lowest values | *Analyses → Comparaison pays (F4)* |
| **F5** | Compare up to 4 series (indicator × country × breakdown), optionally in base 100 | *Analyses → Multi-indicateurs (F5)* |
| **F6** | User accounts with two roles (user / administrator), administration area | *Se connecter*, *Créer un compte*, *Administration* |
| **FO2** | Interactive world map coloured by the value of an indicator | *Analyses → Carte du monde (FO2)* |
| **FO3** | Downloadable PDF report: chart, statistics, ranking and conclusion | *Analyses → Rapport PDF (FO3)* |

The analyses are reserved for logged-in users: a visitor only sees the home page, the login page and
the sign-up page.

---

## Data

Three quarterly ILOSTAT indicators are imported, for about 80 countries, from 2020 onwards:

| Code | Indicator | Unit | Breakdown |
|---|---|---|---|
| `EMP_5EMP_SEX_OC2_NB_Q` | Employment by sex and occupation | thousands | occupation |
| `EMP_5WAP_SEX_AGE_RT_Q` | Employment-to-population ratio by sex and age | % | age group |
| `UNE_5EAP_SEX_AGE_RT_Q` | Unemployment rate by sex and age | % | age group |

Every value can also be filtered by sex (*Total*, *Male*, *Female*).
The list of indicators, countries and the first year are set in a single file,
[`backend/src/config_import.py`](backend/src/config_import.py): add a line there and re-run the import
to follow a new indicator or country.

---

## Quick start on Onyxia

Follow these steps in order. Commands are run in the terminal of the VSCode service, from the project root
(`Projet-Info-2A-grp-17/`) unless a `cd` says otherwise.

### 1. Start a PostgreSQL service

In Onyxia, launch a **PostgreSQL** service. Its README shows the *host*, *port*, *database*, *user* and
*password* you will need in step 3.

### 2. Start a VSCode-python service

Launch a **VSCode-python** service, as in the course practicals:
- in the *Networking* tab, open the ports **5000** (API) and **8000** (interface);
- in the *Git* tab, give the repository URL and tick *clone*.

Open VSCode, then a terminal (*Terminal → New Terminal*). If `uv --version` fails, install it with
`pip install uv`.

### 3. Create the `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in the five `POSTGRES_` values that are empty, using the README of the PostgreSQL
service (step 1). Leave the other lines as they are. Each variable is explained in the file.

### 4. Install the dependencies

The backend and the frontend are two separate projects, each with its own dependencies:

```bash
cd backend && uv sync && cd ..
cd frontend && uv sync && cd ..
```

### 5. Create the database and import the data

```bash
cd backend/src
uv run python -m utils.reset_database      # creates the tables (empty) and the default accounts
uv run python -m fetcher.charger_donnees   # downloads the data from the ILOSTAT API (a few minutes)
cd ../..
```

`reset_database` deletes everything (data **and** accounts): run it only the first time, or to start
again from scratch. The import can be re-run at any time: existing values are updated, never duplicated.

### 6. Start the API and the interface

Open **two terminals** and leave them open:

```bash
# Terminal 1: API
cd backend/src
uv run python main.py
```

```bash
# Terminal 2: interface
cd frontend
uv run streamlit run src/app.py
```

`Ctrl+C` stops a server.

### 7. Open the application

Back on the Onyxia *My services* page, click *Open* on the VSCode service: Onyxia shows one link per port.
- **port 8000**: the application — log in with one of the accounts below;
- **port 5000**: the API and its interactive documentation (`/docs`).

---

## Accounts and roles

Two accounts are created by every database reset (step 5), so you can log in straight away:

| Pseudo | Password | Role |
|---|---|---|
| `user` | `user` | user |
| `admin` | `admin` | administrator |

These passwords are deliberately simple for the demo: change or delete these accounts for a real
deployment.

| | Visitor | User | Administrator |
|---|:---:|:---:|:---:|
| Home page, log in, create an account | ✅ | — | — |
| All analyses (F3, F4, F5, map, PDF report, data explorer) | ❌ | ✅ | ✅ |
| Manage accounts, data, logs and history | ❌ | ❌ | ✅ |

- **Sign-up** (*Créer un compte*) always creates a *user* account: pseudo of 1 to 30 characters,
  password of at least 8 characters. Only an administrator can create another administrator.
- **Sessions**: logging in returns a token, kept by the interface and sent with every request.
  *Se déconnecter* (bottom of the side menu) invalidates it; if the token is no longer valid
  (e.g. the account was deleted), the interface goes back to the visitor menu.
- **Security**: passwords are stored hashed (bcrypt), never in clear text, and are masked in the logs.
  A wrong pseudo and a wrong password give the same message, so accounts cannot be guessed.

---

## Using the application

Once logged in, the *Analyses* section of the side menu contains:

| Page | What you can do |
|---|---|
| **Explorer les données** | Browse the raw observations of an indicator, filtered by country, sex and breakdown |
| **Évolution (F3)** | Choose an indicator, a breakdown and one or more countries, then the number of quarters (2 to 20): line chart of the values, chart of the change from one quarter to the next, detailed table |
| **Comparaison pays (F4)** | Rank all countries on an indicator, at the latest period of each country or at the latest period common to all; highest and lowest values highlighted |
| **Carte du monde (FO2)** | Same comparison drawn on a world map; countries without data stay white |
| **Multi-indicateurs (F5)** | Build up to 4 series (indicator, country, breakdown, sex) and draw them on one chart; *base 100* puts series with different units on the same scale (first common period = 100). Indicators with different frequencies cannot be mixed |
| **Rapport PDF (FO3)** | Choose an indicator, countries, a breakdown, a sex and a number of periods: preview the report (chart, statistics per country, ranking, conclusion) and download it as a PDF |

Every selector only offers values that exist in the database, so a chart is never empty because of a
wrong choice.

---

## Administration

Administrators see an extra *Administration* section:

| Page | What you can do |
|---|---|
| **Utilisateurs** | List all accounts, create an account with any role, delete an account (with confirmation; an administrator cannot delete their own account) |
| **Données** | Re-run the full ILOSTAT import (with confirmation); find an observation with filters, then modify its value or delete it |
| **Logs et historique** | *Historique des actions*: every significant action (log-in, failed log-in, log-out, account creation and deletion, import, modification, deletion), with date and author, filterable by action and pseudo. *Logs techniques*: the last lines of the API log file, filterable by level, downloadable |

---

## Highlights

Beyond the required features, LaborScope offers:

- **Action history**: every important action is recorded in the database with its author, and visible by administrators.
- **Technical logs readable from the interface**: no need to open the server to see what happened; passwords and tokens are always masked.
- **Role-based menu**: each user only sees the pages they are allowed to use, and the API enforces the same rules (a request without a valid token gets `401`, a user calling an admin route gets `403`).
- **World map** and **PDF report** (optional features FO2 and FO3).
- **Base 100 comparison** of indicators with different units (F5).
- **Idempotent import**: re-importing never creates duplicates; the indicators to follow are set in one file.
- **Interactive API documentation** at `/docs`, with an *Authorize* button to test protected routes.

---

## Project structure

```
Projet-Info-2A-grp-17/
├── .env.example          # configuration template (copy to .env)
├── backend/              # FastAPI API, ILOSTAT import, business logic, database access
│   ├── README.md         # developer guide: architecture, endpoints, auth, tests
│   ├── pyproject.toml    # backend dependencies and tool settings (pytest, ruff, pylint)
│   ├── logging_config.yml
│   └── src/
│       ├── main.py               # entry point of the API
│       ├── config_import.py      # indicators, countries and first year to import
│       ├── business_object/      # business classes (Indicateur, Observation, Utilisateur...)
│       ├── dao/                  # SQL queries (one DAO per table)
│       ├── service/              # business logic (analyses, accounts, report...)
│       ├── controller/           # API routes, one file per theme, and access guards
│       ├── schema/               # request and response models (pydantic)
│       ├── fetcher/              # ILOSTAT download and cleaning (F1, F2)
│       ├── utils/                # database reset, logs, password hashing
│       └── tests/                # unit tests, mirroring the folders above
├── frontend/             # Streamlit interface
│   ├── README.md         # developer guide: pages, API client, helpers
│   ├── pyproject.toml
│   ├── .streamlit/       # Streamlit settings (port 8000, theme)
│   └── src/
│       ├── app.py                # entry point: builds the menu according to the role
│       ├── pages/                # one file per page
│       └── utils/                # API client, session, shared selectors
├── data/
│   ├── init_db.sql       # database schema (star schema + users + action history)
│   └── pop_db.sql        # small sample of real data, for troubleshooting only
└── doc/                  # report, design diagrams, weekly follow-up
```

More details for developers: [`backend/README.md`](backend/README.md) and
[`frontend/README.md`](frontend/README.md).

---

## Tests and code quality

```bash
cd backend
uv run pytest           # unit tests
uv run pylint src       # code quality (target 10/10)
uv run ruff check src   # style and imports
```

The DAO tests use the real database: on Onyxia they run, elsewhere (database unreachable) they are
skipped and the reason is displayed. The other tests replace the database and the ILOSTAT API by fakes,
so they run anywhere.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Impossible de joindre le backend` in the interface | The API is not running: start it (step 6, terminal 1) and check `BACKEND_URL` in `.env` |
| Every page shows an error, or log-in fails with a server error | The API cannot reach the database: check the `POSTGRES_` values in `.env`, that the PostgreSQL service is running, then restart the API |
| The menu only shows *Se connecter* | You are not logged in, or your session ended: log in again |
| `Connexion requise` (401) in `/docs` | Log in with `POST /login`, copy the token, click *Authorize* and paste it |
| Pages are empty / no indicator to choose | The database has no data: run the import (step 5) |
| The ILOSTAT API is unreachable | `uv run python -m utils.reset_database --exemple` (from `backend/src`) also loads `data/pop_db.sql`, a small extract of real ILOSTAT data (3 indicators, 6 countries, since 2023). A later import completes it without duplicates |
| Port already in use | A server is still running in another terminal: stop it with `Ctrl+C` |

---

## Authors

ENSAI 2nd-year IT project, group 17:

| Member | Main contribution |
|---|---|
| Clarence | ILOSTAT import and data cleaning (F1, F2), data administration, logs |
| Laurent | User accounts, roles and security (F6), action history, interface skeleton |
| Antifa | Evolution of an indicator (F3) |
| William | Country comparison and world map (F4, FO2) |
| Christian | Multi-indicator comparison and PDF report (F5, FO3) |
