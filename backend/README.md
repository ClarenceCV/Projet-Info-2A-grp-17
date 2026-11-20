# LABORSCOPE

API REST construite avec **FastAPI** pour gérer les ressources de l'application.

## Stack technique

- **Runtime / Framework :** Node.js 22 / Express
- **Base de données :** PostgreSQL
- **ORM / Migration :** Prisma (ou TypeORM / SQLAlchemy)
- **Authentification :** bcrypt

## Prérequis

- Node.js >= 22.x
- PostgreSQL >= 15.x (ou Docker)
- npm / pnpm / yarn

## Installation et démarrage en local

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com
   cd backend/src
   ```

2. **Installer les dépendances**
   ```bash
   npm install
   ```

3. **Configurer les variables d'environnement** (ouverture d'un service POSTGRESQL nécessaire)
   Copiez le fichier exemple et renseignez vos valeurs :
   ```bash
   cp .env.example .env
   ```

4. **Préparer la base de donnée :** une seule fois au début ou si vous voulez reset les données (observations et utilisateurs)
```bash
cd backend/src
uv run python -m utils.reset_database      # recrée les tables (vides) et les comptes par défaut
uv run python -m fetcher.charger_donnees   # importe les données depuis l'API ILOSTAT
```

5. **Démarrer le serveur en développement**
   ```bash
   bakcend/src
   uv run python main.py
   ```
   L'API est accessible sur `http://localhost:5000`.

## Variables d'environnement

| Variable | Description | Exemple |
| :--- | :--- | :--- |
| `PORT` | Port d'écoute du serveur | `5000` |
| `DATABASE_URL` | Chaîne de connexion PostgreSQL | `postgresql://user:pass@localhost:5432/db` |
| `JWT_SECRET` | Clé secrète pour signer les tokens | `votre_cle_secrete` |

## Endpoints principaux

| Méthode | Route | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Non | Vérifie l'état du service |
| `POST` | `/api/auth/login` | Non | Authentifie un utilisateur et retourne un token |
| `GET` | `/api/items` | Oui | Liste les éléments |
| `POST` | `/api/items` | Oui | Crée un nouvel élément |

## Tests

```bash
npm test
```

## Licence

Ce projet est sous licence **MIT**.