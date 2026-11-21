# LaborScope — Frontend (developer guide)

Streamlit interface of LaborScope. It holds **no business logic and no database access**:
every piece of data comes from the backend API, through a single HTTP client.

To install and run the whole application, see the [root README](../README.md).
For the API itself, see [`backend/README.md`](../backend/README.md).

---

## Tech stack

| Package | Use |
|---|---|
| `streamlit` | web interface, multi-page navigation |
| `plotly` | interactive charts and world map |
| `pandas` | tables built from the API answers |
| `requests` | calls to the API |
| `python-dotenv` | reads `BACKEND_URL` and `BACKEND_TIMEOUT` from the root `.env` |

Settings in [`.streamlit/config.toml`](.streamlit/config.toml): port **8000** (5000 is used by the API),
headless mode, theme colour.

```bash
cd frontend
uv sync                            # install
uv run streamlit run src/app.py    # run (the API must be running)
```

---

## Structure

```
frontend/src/
├── app.py                  # entry point: checks the session, builds the menu according to the role
├── pages/
│   ├── accueil.py          # home page (everyone)
│   ├── connexion.py        # log in                       (visitor)
│   ├── creer_compte.py     # sign up                      (visitor)
│   ├── explorer.py         # raw observations             (user)
│   ├── evolution.py        # F3                           (user)
│   ├── comparaison_pays.py # F4                           (user)
│   ├── carte.py            # FO2 world map                (user)
│   ├── multi_indicateurs.py# F5                           (user)
│   ├── rapport.py          # FO3 PDF report               (user)
│   ├── admin_utilisateurs.py # accounts                   (admin)
│   ├── admin_donnees.py    # import, edit / delete data   (admin)
│   └── admin_logs.py       # action history, technical logs (admin)
└── utils/
    ├── api_client.py       # the only HTTP client to the API (adds the token)
    ├── session.py          # log in / log out, error messages
    ├── auth_guard.py       # session check and page guards
    └── selecteurs.py       # shared drop-down menus (indicator, country, breakdown, sex)
```

---

## How a page is displayed

`app.py` runs on **every** click:

1. `verifier_session()` asks the API (`GET /utilisateurs/moi`) whether the token is still valid.
   If not (`401`: logged out elsewhere, account deleted, database reset), the session is forgotten.
   If the API is unreachable, nothing changes: nobody is logged out because of an outage.
2. The menu is built from `st.session_state["role"]`: visitor (`None`), `utilisateur` or `admin`.
3. `st.navigation(menu).run()` runs the chosen page.

Session state, filled by `utils/session.py` at log-in:

| Key | Content |
|---|---|
| `token` | session token returned by `POST /login`, sent with every request |
| `pseudo` | pseudo of the logged-in user |
| `role` | `utilisateur` or `admin` |

---

## Utilities

### `api_client` — every call to the API

```python
from utils.api_client import api_client

reponse = api_client.get("/observations", params={"indicateur": "EMP_5WAP_SEX_AGE_RT_Q"})
# reponse = {"status_code": 200, "data": [...]}
```

- `get`, `post`, `put`, `delete` add the **`X-Auth-Token`** header automatically when someone is logged in.
- They **never raise**: errors come back in the dictionary, with `status_code = 0` when the API is unreachable
  or too slow.
- `telecharger_rapport(...)` returns the raw bytes of the PDF report.

### `session` — errors and log-in

| Function | Use |
|---|---|
| `donnees_ou_arret(reponse)` | returns `reponse["data"]` if the status is 200, otherwise shows the error and stops the page |
| `message_erreur(reponse)` | readable message of a failed answer (the API `detail`, or the connection problem) |
| `connecter_et_ouvrir_accueil(pseudo, mdp)` | logs in, then opens the home page; shows the error on failure |
| `deconnecter()` | invalidates the token in the API, then forgets the session |

### `auth_guard` — page guards

Called at the very top of a page:

```python
from utils.auth_guard import exiger_connexion   # analysis pages
from utils.auth_guard import exiger_admin       # administration pages
exiger_connexion()
```

They only avoid showing a page that would not work. **The real security is in the API**, which answers
`401` / `403` to any request without the right token.

### `selecteurs` — shared drop-down menus

`choisir_indicateur`, `choisir_pays`, `choisir_classif1`, `choisir_sexe`, and `choisir_filtres` (all four
at once). They only offer values that exist in the database (read from `/indicateurs`, `/pays`,
`/indicateurs/{code}/classif1`), cached for 10 minutes. Pass a different `cle` when the same menu appears
twice on a page.

---

## Adding a page, step by step

1. Create `src/pages/my_page.py` with a module docstring.
2. Put the right guard at the top: `exiger_connexion()` or `exiger_admin()`.
3. Read the data through `api_client` and `donnees_ou_arret` (never call `requests` directly).
4. Reuse `selecteurs` for the menus.
5. Add the page to the right list in `app.py` (`pages_analyses` or `pages_admin`), with a title and an icon.

---

## Code quality

```bash
cd frontend
uv run pylint src       # target 10/10
uv run ruff check src
```

Same rules as the backend: maximum line length 100, a docstring for every module and function.
Pages are scripts, so their module-level variables are written in `snake_case`
(allowed by `const-rgx` in [`pyproject.toml`](pyproject.toml)).
