# Projet info - groupe 17 : LaborScope 

## Présentation de projet

LaborScope est une application interactive qui analyse du marché du travail mondial à partir des données de l'OIT ([ILOSTAT](https://ilostat.ilo.org)).
Elle possède au total 8 fonctionnalités:

- F1: Extrait les données de l'API d'ILOSTAT
- F2: Nettoie est stocks les données récupérées 
- F3: Réalise une analyse temporelle selon un indicateur sur un pays.
- F4: Réalise une analyse temporelle selon un indicateur pour plusieurs pays
      et les compare
- F5: Compare des analyses temporelles d'indicateurs différents (jusqu'à 4)
      pour un pays.
- F6: Permet la dynamique d'utilisateur et d'administrateu ainsi que
      la création de compte
- FO2: Observation d'une carte interactive qui représente plusieurs pays
      selon leur valeur sur un indicateur
- FO3: Création de rapports statistique sur un pays et ses valeurs selon
      un indicateur.

## Packages utilisés

### Backend

### Frontend

## Base de donnée

## Architecture du projet

Le projet est organisé en deux parties principales :

log/: permet de suivre toutes les interactions dans l'application

backend/ : contient l'API, la logique métier et les interactions avec la base de données.

frontend/ : contient l'interface utilisateur et les interactions avec l'API.

D'autres dossier son utiliser comme .github qui contient la configuration d'une intégration continue avec Github Actions.

## Lancer l'application sur Onyxia


1. **Lancer un service PosteGreSQL** (Le README du service ontient host, user, mot de passe pour le .env après).
2. **Lancer un service python comme dans le tp** : ouvrir les ports **5000** (API) et **8000** (interface) et connecter au repo git en cochant "clone".
3. Créer et Remplir le fichier **`.env`** (à la racine) en s'insiprant de ça :
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
   BACKEND_TIMEOUT=10
   ```

---

4. Mettre à jour le code et les dépendances
```bash
git pull
uv sync
```

5. Préparer la base de donnée : une seule fois au début ou si vous voulez reset les données (observations et utilisateurs)
```bash
cd backend/src
uv run python -m utils.reset_database      # supprime et recrée toutes les tables, puis les comptes par défaut
uv run python -m fetcher.charger_donnees   # importe les données ILOSTAT 
```
Comptes créés à chaque reset, pour se connecter tout de suite :

| Pseudo | Mot de passe | Rôle |
|---|---|---|
| `user` | `user` | utilisateur |
| `admin` | `admin` | administrateur |

6. Lancer l'API et l'interface (deux terminaux, à laisser ouverts)
```bash
# Terminal 1 : API
cd backend/src
uv run python main.py
```
```bash
# Terminal 2 : interface
cd frontend
uv run streamlit run src/app.py
```
`Ctrl+C` pour arrêter un serveur.

7. Ouvrir dans le navigateur
Retourner sur vos services Onyxia. Cliquer sur "Ouvrir" puis Onyxia affiche un lien par port.
- **port 8000** : l'application ;
- **port 5000** : l'API et sa documentation interactive


---

## Tests
```bash
uv run pytest backend/src/tests
```

---
