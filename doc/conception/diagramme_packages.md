# Diagramme de packages — LaborScope

Une flèche `A --> B` signifie « A importe / utilise B ».
Flèches pleines : dépendances principales (architecture en couches).
Flèches en pointillés : dépendances secondaires.

```mermaid
flowchart TB
    %% ---------------- Frontend ----------------
    subgraph FRONT["frontend/src (Streamlit, port 8000)"]
        APP["app.py<br/>(navigation)"]
        subgraph PAGES["pages"]
            P1["accueil, connexion, creer_compte, explorer<br/>evolution, comparaison_pays, carte<br/>multi_indicateurs, rapport<br/>admin_donnees, admin_logs, admin_utilisateurs"]
        end
        subgraph FUTILS["utils"]
            F1["api_client, auth_guard<br/>selecteurs, session"]
        end
    end

    %% ---------------- Backend ----------------
    subgraph BACK["backend/src (FastAPI, port 5000)"]
        MAIN["main.py<br/>(include_router)"]
        subgraph CONTROLLER["controller"]
            C1["auth, login, utilisateur, admin_utilisateur, admin_donnees<br/>indicateur, pays, observation, journal<br/>evolution, comparaison_pays, multi_indicateurs, rapport"]
        end
        subgraph SCHEMA["schema (modèles Pydantic)"]
            S1["indicateur_model, pays_model, observation_model<br/>utilisateur_model, journal_model<br/>comparaison_pays_model, multi_indicateurs_model"]
        end
        subgraph SERVICE["service (logique métier)"]
            SV1["indicateur, pays, observation, utilisateur, journal<br/>evolution, comparaison_pays, multi_indicateurs, rapport"]
        end
        subgraph DAO["dao (accès à la base)"]
            D1["db_connection<br/>indicateur_dao, pays_dao, observation_dao<br/>utilisateur_dao, journal_dao"]
        end
        subgraph BO["business_object"]
            B1["indicateur, pays, utilisateur<br/>selection, action_journal"]
        end
        subgraph FETCHER["fetcher (import ILOSTAT)"]
            FE1["charger_donnees, fetcher<br/>parser, data_processing"]
        end
        CONFIG["config_import.py<br/>(indicateurs, pays suivis)"]
        subgraph BUTILS["utils"]
            U1["singleton, securite, log_utils<br/>reset_database, comptes_par_defaut"]
        end
    end

    %% ---------------- Externes ----------------
    DB[("PostgreSQL<br/>schéma laborscope<br/>(data/init_db.sql)")]
    ILO(["API ILOSTAT"])

    %% Frontend
    APP --> PAGES
    PAGES --> FUTILS
    FUTILS -- "HTTP (requests)<br/>en-tête X-Auth-Token" --> MAIN

    %% Backend : couches principales
    MAIN --> CONTROLLER
    CONTROLLER --> SCHEMA
    CONTROLLER --> SERVICE
    SERVICE --> DAO
    SERVICE --> BO
    DAO --> BO
    DAO --> DB

    %% Import des données
    FETCHER --> CONFIG
    FETCHER --> DAO
    FETCHER --> ILO

    %% Dépendances secondaires
    MAIN -.-> BUTILS
    CONTROLLER -.-> BO
    CONTROLLER -. "import admin" .-> FETCHER
    SERVICE -.-> SCHEMA
    DAO -.-> SCHEMA
    DAO -.-> BUTILS
    BUTILS -.-> DAO
```

## Rôle de chaque package

| Package | Rôle |
|---|---|
| `frontend/pages` | Une page Streamlit par fonctionnalité (F3, F4, FO2, F5, FO3, administration…) |
| `frontend/utils` | Client HTTP vers l'API, protection des pages, menus de sélection réutilisés, session |
| `controller` | Endpoints FastAPI : lisent les paramètres, vérifient les droits (`auth`), appellent les services |
| `schema` | Format JSON des entrées / sorties de l'API (Pydantic) |
| `service` | Logique métier (calculs pandas) : ne connaît ni HTTP ni SQL |
| `dao` | Requêtes SQL vers PostgreSQL |
| `business_object` | Objets métier simples (Indicateur, Pays, Utilisateur…) |
| `fetcher` | Import des données depuis l'API ILOSTAT vers la base |
| `utils` (backend) | Connexion unique (singleton), hachage des mots de passe, logs, réinitialisation de la base |
