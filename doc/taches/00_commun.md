# Fiche commune — à lire par tout le monde avant sa fiche personnelle

## 1. Qui fait quoi

| Rôle | Fiche | Fonctionnalités du sujet | Nom |
|---|---|---|---|
| **A** — Données et administration | [A_donnees_admin.md](A_donnees_admin.md) | F1, F2, F6 (données), logs, tests, CI |Clarence | 
| **B** — Utilisateurs, sécurité, squelette frontend | [B_utilisateurs_frontend.md](B_utilisateurs_frontend.md) | F6 (comptes, rôles, historique), Streamlit |Laurent |
| **C** — Évolution d'un indicateur | [C_evolution_F3.md](C_evolution_F3.md) | F3 | |
| **D** — Comparaison entre pays + carte | [D_comparaison_pays_F4_FO2.md](D_comparaison_pays_F4_FO2.md) | F4, FO2 | |
| **E** — Multi-indicateurs + rapport PDF | [E_multi_indicateurs_F5_FO3.md](E_multi_indicateurs_F5_FO3.md) | F5, FO3 | |

C, D et E codent chacun **une fonctionnalité complète, de la base de données jusqu'à l'écran**.
C'est le meilleur moyen de comprendre toute l'architecture.
A et B construisent le socle dont les autres ont besoin (tests, `/pays`, connexion, squelette Streamlit).

---

## 2. Ce qui existe déjà (7 octobre)

L'import des données et un premier webservice fonctionnent de bout en bout :

```
API ILOSTAT ──▶ DataProcessing (fetch → parse → save) ──▶ PostgreSQL ──▶ DAO ──▶ Service ──▶ Controller ──▶ JSON (/docs)
```

### Arborescence

```
backend/src/
├── main.py                  ← webservice FastAPI : branche les controllers (include_router)
├── config_import.py         ← QUOI importer : INDICATEURS, PAYS_SUIVIS, ANNEE_DEBUT
├── business_object/
│   ├── indicateur.py        ← dataclass Indicateur (code, libelle, unite, frequence, nom_classif1)
│   └── pays.py              ← Pays (+ continent(), groupes())
├── fetcher/                 ← tout ce qui concerne l'API externe ILOSTAT
│   ├── fetcher.py           ← construire_url, load_data (téléchargement)
│   ├── parser.py            ← retirer_prefixe (nettoyage des libellés)
│   ├── data_processing.py   ← classe DataProcessing : fetch_data, parse_data, save_data, charger
│   └── charger_donnees.py   ← script d'import (python -m fetcher.charger_donnees)
├── dao/                     ← tout le SQL
│   ├── db_connection.py     ← connexion unique (Singleton) à PostgreSQL
│   ├── indicateur_dao.py    ← enregistrer, lister, trouver_par_code
│   ├── pays_dao.py          ← enregistrer
│   └── observation_dao.py   ← enregistrer, lire (filtres → DataFrame)
├── service/                 ← logique métier (calculs pandas)
├── schema/                  ← format JSON des réponses (Pydantic)
├── controller/              ← endpoints de l'API
└── utils/                   ← reset_database, singleton
data/init_db.sql             ← création des tables
```

### La base de données (modèle en étoile)

```
pays (code_iso PK, nom)                         ex : FRA | France
indicateur (id PK, code UNIQUE, libelle, unite, frequence, nom_classif1)
observation (indicateur_id FK, code_iso FK, source, periode, sexe, classif1,   ← clé primaire (6 colonnes)
             valeur, statut, date_maj)
```

Exemple de ligne d'`observation` (taux d'emploi) :

| indicateur_id | code_iso | source | periode | sexe | classif1 | valeur | statut |
|---|---|---|---|---|---|---|---|
| 2 | FRA | LFS - Employment Survey | 2024Q4 | Female | 15-24 | 30.766 | NULL |

Les deux indicateurs :

| code | libellé | unité | classif1 contient | valeur « total » de classif1 |
|---|---|---|---|---|
| `EMP_5EMP_SEX_OC2_NB_Q` | Emploi par sexe et profession | milliers | une profession (`22 - Health professionals`) | `Total` |
| `EMP_5WAP_SEX_AGE_RT_Q` | Taux d'emploi par sexe et âge | % | une tranche d'âge (`15-24`, `25+`) | `15+` |

`sexe` vaut `Total`, `Male` ou `Female`. `periode` est au format `AAAAQn` (`2024Q4`) : l'ordre alphabétique est aussi l'ordre chronologique.

⚠️ **Plusieurs sources** : un même pays peut avoir plusieurs sources (enquêtes) pour une même période. Dans les analyses, il faut garder **une seule source par pays et par période**, sinon on obtient des courbes en double. Règle commune proposée : garder la première source par ordre alphabétique (`drop_duplicates`).

### Les endpoints qui existent

| Endpoint | Rôle |
|---|---|
| `GET /indicateurs` | liste des indicateurs |
| `GET /indicateurs/{code}` | un indicateur (404 s'il n'existe pas) |
| `GET /observations?indicateur=...&pays=FRA&periode_min=...&sexe=...&classif1=...&limite=...` | observations filtrées |

**`GET /observations` est le modèle à copier** pour tout nouvel endpoint. Suivez son parcours dans le code :

```
controller/observation_controller.py   lister_observations()     ← reçoit la requête, vérifie l'indicateur (404)
  └─ service/observation_service.py    ObservationService.lister()
       └─ dao/observation_dao.py       ObservationDAO.lire()     ← SELECT ... JOIN ... → DataFrame
  ◀─ schema/observation_model.py       ObservationModel          ← DataFrame → to_dict → JSON
```

---

## 3. Faire tourner le projet sur Onyxia (tout le monde, semaine 1)

### Services à lancer (une seule fois)

1. **Mon compte → Git** : renseigner nom, email et un **token GitHub** (GitHub → Settings → Developer settings → Personal access tokens, droit `repo`). Sans token, pas de `git push`.
2. **Catalogue → PostgreSQL → Lancer.** Garder l'onglet README du service : il contient host, port, base, user, mot de passe.
3. **Catalogue → Vscode-python → Configuration → Networking** : activer *Enable a custom service port* et ouvrir les ports **5000** (API) et **8000** (Streamlit). **Lancer.**
4. (Facultatif) **Catalogue → CloudBeaver** pour regarder la base avec une interface graphique.

### Dans le terminal du VSCode Onyxia

```bash
git clone https://github.com/ClarenceCV/Projet-Info-2A-grp-17.git
cd Projet-Info-2A-grp-17               # puis File > Open Folder sur ce dossier
curl -LsSf https://astral.sh/uv/install.sh | sh   # si uv n'est pas installé
uv sync
```

Créer le fichier **`.env`** à la racine (jamais commité) :

```
POSTGRES_HOST=postgresql-xxxxxx
POSTGRES_PORT=5432
POSTGRES_DATABASE=defaultdb
POSTGRES_USER=user-xxxx
POSTGRES_PASSWORD=xxxx
POSTGRES_SCHEMA=laborscope

UVICORN_HOST=0.0.0.0
UVICORN_PORT=5000
BACKEND_URL=http://localhost:5000
```

### Créer la base, importer, lancer l'API

```bash
cd backend/src
uv run python -m utils.reset_database      # crée les tables (vides)
uv run python -m fetcher.charger_donnees   # importe ILOSTAT (~1 min) → ~10 000 observations
uv run python main.py                      # lance l'API (Ctrl+C pour l'arrêter)
```

Ouvrir l'API : **Mes services → VSCode → Ouvrir** → lien du **port 5000** (`https://user-xxx-5000.user.lab.sspcloud.fr`).
⚠️ Ne pas cliquer sur le lien `localhost` de la popup VSCode : il ne marche pas sur Onyxia.

Dans `/docs`, tester `GET /observations` avec `indicateur=EMP_5WAP_SEX_AGE_RT_Q`, `pays=FRA`, `periode_min=2024Q4`, `sexe=Female`, `classif1=15-24` → **30.766**.
**Si vous obtenez ce résultat, votre environnement est prêt.**

### Problèmes fréquents

| Erreur | Cause |
|---|---|
| `KeyError: 'POSTGRES_HOST'` | `.env` absent ou mal placé (il doit être à la racine) |
| `could not translate host name` | mauvais host, ou service PostgreSQL arrêté |
| l'API renvoie une 502 pendant l'import | panne passagère d'ILOSTAT : relancer |
| `ModuleNotFoundError` | lancer les commandes **depuis `backend/src`** |

---

## 4. Règles de travail (sans relecteur)

Tout le monde pousse directement sur `main`. Pour que ça reste vivable :

1. **`git pull` avant de commencer** à travailler, à chaque fois.
2. **Petits commits fréquents**, avec un message clair : `feat: service evolution F3`, `fix: ...`, `test: ...`, `doc: ...`.
3. **Avant chaque `git push`** : `uv run pytest` doit passer, et l'API doit démarrer (`uv run python main.py`).
4. **Conflit au `git pull`** : ouvrir le fichier, garder les deux versions quand c'est possible, retester, commiter. Pour `uv.lock`, relancer simplement `uv lock` puis commiter.
5. **Chacun travaille dans ses propres fichiers** (voir sa fiche). Les **fichiers partagés** ci-dessous se modifient en ajoutant des lignes, sans toucher à celles des autres, et en prévenant le groupe :

| Fichier partagé | Ce que chacun y fait |
|---|---|
| `backend/src/main.py` | ajouter **une ligne** `include_router` pour son controller |
| `data/init_db.sql` | A gère les tables de données, B ajoute `utilisateur` et `journal` |
| `pyproject.toml` / `uv.lock` | `uv add <paquet>` (jamais d'édition à la main) |
| `frontend/app.py` (créé par B) | ajouter **sa page** dans la navigation |

6. **Ne jamais commiter** `.env`, des mots de passe ou des fichiers CSV de test.

---

## 5. La documentation de l'API

Pas de document à écrire pendant le développement :
- **chaque fiche (C, D, E) contient déjà le contrat proposé** de son endpoint (adresse, paramètres, exemple de réponse JSON). B s'en sert pour préparer les pages Streamlit. Si tu veux changer un nom ou un format par rapport à ta fiche, **préviens B** ;
- **`/docs`** (généré automatiquement par FastAPI) est la documentation de référence : elle est toujours à jour avec le code ;
- **en fin de projet** (semaine 5), A liste tous les endpoints dans le README.

---

## 6. Planning global

| Semaine | Objectif |
|---|---|
| **S1 — 7 au 13 oct** | tout le monde fait tourner le projet sur Onyxia et comprend le parcours de `/observations` ; A : tests + `/pays` ; B : squelette Streamlit + gardes provisoires |
| **S2 — 14 au 20 oct** | services + tests |
| **S3 — 21 au 23 oct** | schémas + endpoints, testés dans `/docs` |
| *24 au 31 oct* | vacances |
| **S4 — 2 au 8 nov** | pages Streamlit ; options (FO2, FO3) ; connexion activée partout |
| **S5 — 9 au 14 nov** | corrections, tests, README — **code figé le 14 novembre** |
| **7 au 21 nov** | rédaction du rapport final (chacun ses parties, voir sa fiche) |
| **21 nov au 9 déc** | préparation de la soutenance |

Chaque semaine, chacun complète le fichier de suivi `doc/suivi/AAAA.MM.JJ-semaineN.md` (temps passé + tâches).

---

## 7. Le rapport final : ce qui doit changer par rapport au rapport d'analyse

Le rapport intermédiaire décrit une conception qui a changé. Chaque fiche indique les parties dont la personne est responsable. Les points à corriger :

| Partie du rapport intermédiaire | Problème | Responsable |
|---|---|---|
| 1.3 Structure de la base | « deux bases distinctes » → c'est **un modèle en étoile** (3 tables) | A |
| 2.2 Diagramme de classes | la classe `Observation` n'existe plus (on travaille en DataFrames) ; manquent DAO, controllers, DataProcessing | A (assemblage), chacun fournit ses classes |
| 2.5 Diagramme d'activité utilisateur | « Comparaison entre pays » est rangée sous « Analyse temporelle » ; F3 n'apparaît pas | C |
| 2.6 Diagramme de séquence | exemple du « taux de chômage », qui n'est pas un de nos indicateurs | C |
| 2.1, 2.3, 2.4 (cas d'utilisation, activité globale, admin) | à aligner avec ce qui est réellement codé | B (et A pour « gestion des données ») |

Les diagrammes UML peuvent être écrits en **Mermaid** dans `doc/conception/` (affichés par GitHub et VSCode), puis exportés en image pour le rapport.
