# Fiche A — Données et administration

> **Ton rôle en une phrase** : tu es responsable de tout ce qui touche aux données (import ILOSTAT, base, actions admin sur les données) et de la qualité du projet (tests, logs, CI, README).
> Les autres ont besoin de toi dès la **semaine 1** : sans infrastructure de tests ni `GET /pays`, ils sont ralentis.

Lis d'abord [00_commun.md](00_commun.md).

---

## Tes fichiers

| Fichier | Statut |
|---|---|
| `fetcher/*`, `config_import.py`, `data/init_db.sql` (tables de données) | tu es le référent |
| `dao/pays_dao.py`, `dao/observation_dao.py` (écriture, modification, suppression) | tu complètes |
| `service/pays_service.py`, `service/admin_donnees_service.py` | à créer |
| `controller/pays_controller.py`, `controller/admin_donnees_controller.py` | à créer |
| `schema/pays_model.py`, `schema/admin_model.py` | à créer |
| `utils/log_utils.py`, `logging_config.yml` | à créer / remplir |
| `backend/tests/` (structure + `conftest.py`), `.github/workflows/ci.yml`, `README.md` | à créer |

---

## Étape 0 — Comprendre l'existant (½ journée)

Tu connais déjà le code, mais vérifie que tu sais répondre à ces questions, car C, D et E vont te les poser :

1. Dans `DataProcessing.parse_data`, pourquoi sélectionne-t-on les colonnes **avant** de les renommer ?
2. Pourquoi `save_data` enregistre-t-il l'indicateur, puis les pays, puis les observations, **dans cet ordre** ?
3. Que fait `ON CONFLICT ... DO UPDATE` dans `ObservationDAO.enregistrer`, et pourquoi c'est indispensable pour F1 ?
4. Comment `ObservationDAO.lire` construit-il son `WHERE`, et pourquoi n'y a-t-il pas de risque d'injection SQL ?
5. Pourquoi `ObservationDAO.lire` renvoie-t-il un DataFrame et pas des objets ?

Puis fais tourner le projet sur Onyxia (section 3 de la fiche commune) jusqu'au résultat `30.766`.

---

## Étape 1 — Semaine 1 : le socle pour les autres (PRIORITÉ)

### 1.a Infrastructure de tests

Les autres écriront des tests dès la semaine 2 : il faut que `uv run pytest` fonctionne.

1. Dans `pyproject.toml`, ajouter :
   ```toml
   [tool.pytest.ini_options]
   pythonpath = ["backend/src"]   # pour que "from service.xxx import ..." fonctionne dans les tests
   testpaths = ["backend/tests"]
   ```
2. Créer l'arborescence :
   ```
   backend/tests/
   ├── conftest.py            # vide pour l'instant (ou chargement du .env pour les tests DAO)
   ├── test_service/
   └── test_dao/
   ```
3. Écrire un **premier test d'exemple** que les autres copieront : `backend/tests/test_service/test_observation_service.py`
   ```python
   from unittest.mock import patch

   import pandas as pd

   from dao.observation_dao import ObservationDAO
   from service.observation_service import ObservationService


   def test_lister_renvoie_le_dataframe_du_dao():
       # GIVEN : un faux DAO qui renvoie 2 lignes, sans base de données
       faux_df = pd.DataFrame({"code_iso": ["FRA", "DEU"], "valeur": [1.0, 2.0]})
       with patch.object(ObservationDAO, "lire", return_value=faux_df):
           # WHEN
           res = ObservationService().lister("EMP_5WAP_SEX_AGE_RT_Q", ["FRA", "DEU"])
       # THEN
       assert len(res) == 2
   ```
4. Vérifier : `uv run pytest` depuis la racine → `1 passed`.
5. **Prévenir le groupe** que les tests sont prêts.

### 1.b `GET /pays`

Les menus déroulants de C, D et E en ont besoin.

| Couche | À écrire |
|---|---|
| DAO | `PaysDAO.lister() -> list[Pays]` : `SELECT code_iso, nom FROM laborscope.pays ORDER BY nom` (copier le modèle d'`IndicateurDAO.lister`). Attention : la colonne s'appelle `nom` en base et `nom_pays` dans la classe `Pays`. |
| Service | `PaysService.lister()` |
| Schéma | `PaysModel(code_iso: str, nom_pays: str, continent: str \| None)` — tu peux utiliser `Pays.continent()` |
| Controller | `GET /pays` → `list[PaysModel]` ; ajouter la ligne `include_router` dans `main.py` |

Résultat attendu : `[{"code_iso": "DEU", "nom_pays": "Germany", "continent": "EU"}, ...]`

### 1.b bis `GET /indicateurs/{code}/classif1`

C, D et E ont besoin de proposer à l'utilisateur les valeurs possibles de `classif1` (les professions ou les tranches d'âge d'un indicateur).
- DAO : `ObservationDAO.lister_classif1(code_indicateur) -> list[str]` :
  `SELECT DISTINCT o.classif1 FROM laborscope.observation o JOIN laborscope.indicateur i ON i.id = o.indicateur_id WHERE i.code = %(code)s ORDER BY o.classif1`
- Endpoint dans `indicateur_controller.py` : `GET /indicateurs/{code}/classif1` → `["15+", "15-24", "25+"]` (404 si l'indicateur n'existe pas).

### 1.c Hygiène du dépôt

- **`.env` est encore suivi par git** alors qu'il contient des mots de passe :
  ```bash
  git rm --cached .env
  ```
  et créer un **`.env.example`** (mêmes clés, valeurs vides) que les autres copieront.
- Supprimer ce qui ne sert plus : `business_object/observation.py`, `business_object/profession.py`, `data/data.py` (vide), et dans `fetcher/parser.py` les fonctions `nettoyer`, `mapper`, `separer_classif1` (seule `retirer_prefixe` est utilisée).
  Vérifier ensuite que tout s'importe encore : `uv run python -c "import main"` depuis `backend/src`.

---

## Étape 2 — Semaines 2 et 3 : administration des données (F6, partie données)

Correspond au diagramme d'activité admin → **« Gestion des données »**.

### 2.a Import robuste

Aujourd'hui, une erreur 502 d'ILOSTAT sur **un** pays fait échouer **tout** l'indicateur.
Dans `DataProcessing.fetch_data`, entourer le téléchargement de chaque pays d'un `try/except` :
- réessayer 2 à 3 fois en attendant quelques secondes (`time.sleep`) ;
- si ça échoue encore, afficher (puis logger) un avertissement et **passer au pays suivant**.

Test : `fetch_data` avec un `load_data` simulé qui lève une erreur pour un pays → les autres pays sont quand même renvoyés.

### 2.b Endpoints admin

| Endpoint | Couche DAO | Rôle |
|---|---|---|
| `POST /admin/import` | — | « Forcer le chargement de l'API externe » : appelle `DataProcessing().charger(INDICATEURS)`, renvoie le nombre d'observations importées |
| `PUT /admin/observations` | `ObservationDAO.modifier(cle, nouvelle_valeur) -> bool` | modifier la valeur d'**une** observation, identifiée par sa clé complète (indicateur, code_iso, source, periode, sexe, classif1) ; 404 si elle n'existe pas (`cursor.rowcount == 0`) |
| `DELETE /admin/observations` | `ObservationDAO.supprimer(cle) -> bool` | supprimer une observation ; 404 si elle n'existe pas |

- Le corps de `PUT`/`DELETE` est un modèle Pydantic `CleObservationModel` (les 6 champs de la clé) — c'est l'occasion d'utiliser un corps JSON au lieu de paramètres d'URL.
- Ces endpoints doivent être **réservés aux administrateurs** : ajouter `Depends(admin_requis)` fourni par B (voir sa fiche). Tant que B n'a pas fini, sa version provisoire laisse tout passer.
- Chaque action admin doit être écrite dans le **journal** de B (`JournalService().enregistrer(utilisateur, "modification", "...")`) — à brancher en semaine 4.

⚠️ **Point de conception à documenter dans le rapport** : un import (`POST /admin/import`) écrase les modifications manuelles faites par un admin (l'upsert remet la valeur ILOSTAT). Décide avec le groupe si c'est acceptable et écris-le.

### 2.c (Facultatif) Import périodique automatique

F1 parle de « récupération périodique ». Deux options, à discuter :
- simple : l'admin clique sur « Forcer le chargement » (déjà fait en 2.b) ;
- automatique : `APScheduler` lance `charger` chaque semaine au démarrage de l'API.

### 2.d Pays suivis

D aura besoin de **plus de pays** pour la carte (FO2). Avec D, choisir une liste plus large dans `config_import.PAYS_SUIVIS` (par exemple tous les pays de l'UE + quelques autres), et vérifier que l'import reste raisonnable en temps.

---

## Étape 3 — Semaine 4 : logs techniques

Correspond au diagramme admin → « Gestion de l'application » → **« Lire les logs techniques »**.

1. Remplir `logging_config.yml` (vide aujourd'hui) en s'inspirant du template : un handler console + un handler fichier `logs/laborscope.log`.
2. Reprendre `utils/log_utils.py` du template ([lien](https://github.com/ludo2ne/ENSAI-2A-projet-info-template/blob/main/backend/src/utils/log_utils.py)) : `initialize_logs`, `get_logger`, décorateur `@log`.
3. Appeler `initialize_logs("LaborScope")` au début de `main.py`, et poser `@log` sur les méthodes des services et DAO.
4. Remplacer les `print` de `DataProcessing` par `logger.info(...)` / `logger.warning(...)`.
5. Endpoint admin `GET /admin/logs?lignes=100` : renvoie les N dernières lignes du fichier de log.
6. Ajouter `logs/` au `.gitignore`.

---

## Étape 4 — Semaines 4 et 5 : qualité

### Tests à écrire (tes parties)
| Test | Fichier |
|---|---|
| `parse_data` : renommage, lignes sans valeur supprimées, préfixes retirés, doublons supprimés, DataFrame vide | `test_service/test_data_processing.py` (construire un petit DataFrame brut à la main, 3-4 lignes) |
| `fetch_data` : un pays en erreur n'arrête pas les autres | idem, avec `load_data` simulé |
| services admin avec DAO simulé | `test_service/test_admin_donnees_service.py` |
| (bonus) DAO sur une vraie base | `test_dao/` — à lancer seulement sur Onyxia |

### CI GitHub Actions
Créer `.github/workflows/ci.yml` en s'inspirant de celui du template : à chaque push, installer uv, `uv sync`, `uv run pytest`, puis `uv run ruff check backend/src` (ajouter `ruff` en dépendance de dev : `uv add --dev ruff`).
Ne lancer en CI que les tests de **service** (pas de base de données sur GitHub).

### README
Réécrire `README.md` (aujourd'hui presque vide) : présentation, installation sur Onyxia, `.env`, commandes (reset, import, API, Streamlit), liste des endpoints, structure du projet. S'inspirer du README du template.

---

## Étape 5 — Rapport final : tes parties

| Partie | Contenu |
|---|---|
| **Architecture technique** | mettre à jour le diagramme d'architecture (figure 1.1) : le bloc « Récupération / Traitement » devient `fetcher/DataProcessing` |
| **Structure de la base de données** (remplace 1.3) | modèle en étoile, **diagramme SQL** des tables (`pays`, `indicateur`, `observation`, + `utilisateur` et `journal` fournis par B), clé primaire composée, upsert, choix « libellés en base » et sa limite (si ILOSTAT renomme un libellé → doublons) |
| **Récupération et stockage (F1, F2)** | le pipeline fetch → parse → save, les problèmes rencontrés (BOM, curl bloqué, sources multiples, valeurs manquantes) et leurs solutions |
| **Gestion des données par l'administrateur** | endpoints admin, conflit import / corrections manuelles |
| **Diagramme de classes global** | **tu l'assembles** : chacun t'envoie ses classes (en Mermaid), tu produis le diagramme complet, découpé par couche |
| **Tests et qualité** | stratégie de tests (services avec DAO simulés), CI, logs |
| **Annexe : installation** | reprise du README |

Supprimer du rapport : la classe `Observation`, « deux bases distinctes ».

---

## Checklist

- [ ] S1 : `uv run pytest` fonctionne + test d'exemple — **prévenir le groupe**
- [ ] S1 : `GET /pays` et `GET /indicateurs/{code}/classif1`
- [ ] S1 : `.env` retiré de git, `.env.example`, ancien code supprimé
- [ ] S2 : import robuste (erreurs par pays)
- [ ] S2-S3 : `POST /admin/import`, `PUT`/`DELETE /admin/observations`
- [ ] S2-S3 : liste de pays élargie avec D
- [ ] S4 : logs + `GET /admin/logs` + journal branché
- [ ] S4-S5 : tests `parse_data`/`fetch_data`, CI, README
- [ ] Rapport : architecture, base de données, F1-F2, admin données, diagramme de classes global, tests

## Tu dépends de / tu fournis à

- **Tu fournis** : tests (tout le monde, S1), `GET /pays` et `GET /indicateurs/{code}/classif1` (B, C, D, E), liste de pays élargie (D), diagramme de classes global (rapport).
- **Tu dépends de B** : `admin_requis` (provisoire dès S1) et `JournalService` (S4).
