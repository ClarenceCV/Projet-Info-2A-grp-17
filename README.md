# Projet info - groupe 17 : LaborScope 

Analyse interactive du marché du travail mondial à partir des données de l'OIT ([ILOSTAT](https://ilostat.ilo.org)).



## LAncer l'application sur Onyxia


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

5. Préparer la base (seulement si nécessaire) : une fois au début ou si vous voulez reset les données (observations et utilisateurs)
```bash
cd backend/src
uv run python -m utils.reset_database      # supprime et recrée toutes les tables (vides)
uv run python -m fetcher.charger_donnees   # importe les données ILOSTAT 
```

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
`Ctrl+C` arrête un serveur.

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
