# Fiche B — Utilisateurs, sécurité et squelette frontend

> **Ton rôle en une phrase** : tu gères les comptes (création, connexion, rôles utilisateur / administrateur, historique des actions) et tu construis le **squelette de l'application Streamlit** dans lequel chacun ajoutera sa page.
> Les autres ont besoin de toi dès la **semaine 1** : les gardes d'authentification (même provisoires) et le squelette Streamlit.

Lis d'abord [00_commun.md](00_commun.md).

---

## Tes fichiers

| Fichier | Statut |
|---|---|
| `data/init_db.sql` (tables `utilisateur` et `journal`) | tu ajoutes |
| `business_object/utilisateur.py` | à créer |
| `dao/utilisateur_dao.py`, `dao/journal_dao.py` | à créer |
| `service/utilisateur_service.py`, `service/journal_service.py` | à créer |
| `schema/utilisateur_model.py` | à créer |
| `controller/auth.py` (gardes), `controller/utilisateur_controller.py`, `controller/admin_utilisateur_controller.py` | à créer |
| `frontend/` (tout le squelette) | à créer |

---

## Étape 0 — Comprendre l'existant (½ journée)

1. Faire tourner le projet sur Onyxia (section 3 de la fiche commune) jusqu'au résultat `30.766`.
2. Relire le parcours de `GET /observations` (controller → service → DAO) : tu vas reproduire exactement ce schéma pour les utilisateurs.
3. Dans le template, lire : `backend/src/controller/login_controller.py`, `backend/src/utils/security.py`, `frontend/src/utils/api_client.py`, `frontend/src/utils/auth_guard.py`, `frontend/src/app.py`. Tu vas t'en inspirer fortement.
4. Relire les diagrammes d'activité du rapport intermédiaire (2.3 global, 2.4 admin, 2.5 utilisateur) : c'est la navigation que tu vas coder.

---

## Étape 1 — Semaine 1 : ce dont les autres ont besoin (PRIORITÉ)

### 1.a Gardes d'authentification provisoires

Tous les endpoints devront vérifier qui appelle. Crée tout de suite `controller/auth.py` avec deux fonctions que les autres utiliseront dans leurs controllers :

```python
# controller/auth.py — version PROVISOIRE (semaine 1) : laisse tout passer
from fastapi import Header


def utilisateur_connecte(x_auth_token: str | None = Header(None)):
    """Renvoie l'utilisateur correspondant au token. Provisoire : renvoie toujours un admin fictif."""
    return {"pseudo": "dev", "role": "admin"}


def admin_requis(x_auth_token: str | None = Header(None)):
    """Vérifie que l'utilisateur est administrateur. Provisoire : laisse tout passer."""
    return utilisateur_connecte(x_auth_token)
```

Utilisation par les autres :
```python
from fastapi import Depends
from controller.auth import admin_requis

@router.post("/import")
async def forcer_import(utilisateur=Depends(admin_requis)):
    ...
```
**Prévenir le groupe** dès que c'est poussé. En semaine 3, tu remplaces le contenu par la vraie vérification, **sans changer les noms** : le code des autres n'aura rien à modifier.

### 1.b Squelette Streamlit

Structure proposée (inspirée du template) :

```
frontend/
├── app.py                 ← point d'entrée : navigation selon le rôle (diagrammes d'activité)
├── .streamlit/config.toml ← port 8000, réglages pour Onyxia
├── pages/
│   ├── accueil.py         ← choix : se connecter / créer un compte
│   ├── connexion.py
│   ├── creer_compte.py
│   ├── evolution.py       ← page de C (vide au début : "en construction")
│   ├── comparaison_pays.py← page de D
│   ├── carte.py           ← page de D
│   ├── multi_indicateurs.py ← page de E
│   ├── rapport.py         ← page de E
│   ├── admin_utilisateurs.py ← ta page
│   ├── admin_donnees.py   ← page de A
│   └── admin_logs.py      ← page de A (logs + historique)
└── utils/
    ├── api_client.py      ← TOUS les appels HTTP au backend (ajoute le token automatiquement)
    ├── auth_guard.py      ← bloque une page si pas connecté / pas admin
    └── selecteurs.py      ← composants communs : choisir un indicateur, des pays, une période, un sexe
```

À faire :
1. `uv add streamlit plotly`
2. `api_client.py` : une fonction `get(chemin, params)` et `post(chemin, json)` qui appellent `BACKEND_URL` (du `.env`) et ajoutent l'en-tête `X-Auth-Token` à partir de `st.session_state["token"]`.
3. `selecteurs.py` : `choisir_indicateur()` (appelle `GET /indicateurs`), `choisir_pays(multiple=True)` (appelle `GET /pays` de A), `choisir_sexe()`, `choisir_classif1(code_indicateur)` (appelle `GET /indicateurs/{code}/classif1` de A). **C, D et E les réutiliseront** : ça évite que chacun recode les mêmes menus.
4. `app.py` avec `st.navigation` : menu utilisateur (Évolution, Comparaison pays, Carte, Multi-indicateurs, Rapport) et, **si admin**, menu administrateur en plus. Pour l'instant toutes les pages affichent « en construction ».
5. Lancer sur Onyxia (port 8000) :
   ```bash
   cd frontend
   uv run streamlit run app.py --server.port 8000 --server.address 0.0.0.0
   ```
   puis ouvrir le lien du **port 8000** dans Mes services. Si la page reste blanche ou affiche une erreur de WebSocket derrière le proxy Onyxia, ajouter dans `.streamlit/config.toml` : `enableCORS = false` et `enableXsrfProtection = false` (section `[server]`).
6. **Prévenir le groupe** : chacun pourra remplacer « en construction » par sa page.

---

## Étape 2 — Semaines 2 et 3 : comptes et connexion (F6)

### 2.a Tables SQL (ajouter à la fin de `init_db.sql`)

```sql
CREATE TABLE utilisateur (
    id                 SERIAL PRIMARY KEY,
    pseudo             TEXT NOT NULL UNIQUE,
    mot_de_passe_hash  TEXT NOT NULL,             -- jamais le mot de passe en clair
    role               TEXT NOT NULL DEFAULT 'utilisateur' CHECK (role IN ('utilisateur', 'admin')),
    token              TEXT UNIQUE,               -- jeton de session, NULL si déconnecté
    date_creation      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE journal (
    id              SERIAL PRIMARY KEY,
    utilisateur_id  INT REFERENCES utilisateur(id) ON DELETE SET NULL,
    action          TEXT NOT NULL,                -- 'connexion', 'creation_compte', 'suppression_donnee'...
    detail          TEXT,
    date            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.b Les couches

| Couche | À écrire |
|---|---|
| Objet métier | `Utilisateur` (dataclass) : `pseudo`, `role`, `id` (le hash ne sort jamais du DAO/service) |
| DAO | `UtilisateurDAO` : `creer`, `trouver_par_pseudo`, `trouver_par_token`, `lister`, `supprimer`, `enregistrer_token` ; `JournalDAO` : `enregistrer`, `lister` |
| Service | `UtilisateurService` : `creer_compte(pseudo, mdp)` (hache avec **bcrypt**), `se_connecter(pseudo, mdp)` (vérifie le hash, génère un token avec `secrets.token_urlsafe(32)`), `se_deconnecter(token)` ; `JournalService.enregistrer(utilisateur, action, detail)` |
| Schéma | `CreationCompteModel(pseudo, mot_de_passe)`, `ConnexionModel`, `UtilisateurModel(id, pseudo, role)` **sans mot de passe**, `TokenModel(token, role)` |
| Controller | voir tableau ci-dessous |

bcrypt (`uv add bcrypt`) :
```python
import bcrypt
hash_ = bcrypt.hashpw(mot_de_passe.encode(), bcrypt.gensalt()).decode()      # à la création
ok = bcrypt.checkpw(mot_de_passe.encode(), hash_.encode())                  # à la connexion
```

### 2.c Endpoints

| Endpoint | Accès | Rôle |
|---|---|---|
| `POST /utilisateurs` | public | créer un compte — **toujours** avec le rôle `utilisateur` (le rapport précise qu'un utilisateur ne peut pas devenir admin) ; 400 si pseudo déjà pris |
| `POST /login` | public | renvoie `{token, role}` ; 401 si identifiants faux |
| `POST /logout` | connecté | efface le token |
| `GET /utilisateurs/moi` | connecté | qui suis-je |
| `GET /admin/utilisateurs` | admin | liste |
| `POST /admin/utilisateurs` | admin | créer un utilisateur **ou un administrateur** |
| `DELETE /admin/utilisateurs/{id}` | admin | supprimer |
| `GET /admin/journal` | admin | historique des actions (« Lire l'historique des utilisateurs ») |

### 2.d Remplacer les gardes provisoires (fin S3)

```python
def utilisateur_connecte(x_auth_token: str | None = Header(None)) -> Utilisateur:
    utilisateur = UtilisateurService().trouver_par_token(x_auth_token) if x_auth_token else None
    if utilisateur is None:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    return utilisateur

def admin_requis(utilisateur: Utilisateur = Depends(utilisateur_connecte)) -> Utilisateur:
    if utilisateur.role != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs.")
    return utilisateur
```
401 = « pas connecté », 403 = « connecté mais pas le droit ».

### 2.e Le premier administrateur

Personne ne peut créer d'admin sans être déjà admin : prévoir un script `utils/creer_admin.py` (pseudo + mot de passe lus dans le `.env` : `ADMIN_PSEUDO`, `ADMIN_PASSWORD`) à lancer après `reset_database`. L'ajouter dans `.env.example` et dans le README (avec A).

---

## Étape 3 — Semaine 4 : frontend connecté

1. Pages `connexion.py` et `creer_compte.py` : appellent `POST /login` / `POST /utilisateurs`, stockent `token` et `role` dans `st.session_state`.
2. `auth_guard.py` : `exiger_connexion()` et `exiger_admin()` à appeler en haut de chaque page.
3. Bouton **Se déconnecter** (diagramme global : « Retour à l'accueil »).
4. Page `admin_utilisateurs.py` : tableau des utilisateurs, formulaire d'ajout (avec choix du rôle), bouton supprimer.
5. Page historique (dans `admin_logs.py`, avec A) : tableau du journal.
6. Brancher le journal : enregistrer `connexion`, `creation_compte`, `suppression_compte`. Donner `JournalService` à A pour les actions sur les données.
7. Vérifier avec C, D, E que leurs pages fonctionnent une fois la connexion activée.

---

## Étape 4 — Tests

| Test | Fichier |
|---|---|
| `creer_compte` hache le mot de passe (le hash ≠ le mot de passe, `checkpw` OK) | `test_service/test_utilisateur_service.py` |
| `creer_compte` refuse un pseudo déjà pris | idem (DAO simulé) |
| `se_connecter` : bon mot de passe → token ; mauvais → `None` | idem |
| `admin_requis` lève 403 pour un utilisateur simple | `test_controller/test_auth.py` (appeler la fonction directement) |

---

## Étape 5 — Rapport final : tes parties

| Partie | Contenu |
|---|---|
| **2.1 Diagramme de cas d'utilisation** | aligner avec ce qui est codé (créer un compte, se connecter, rôles ; un utilisateur ne peut pas devenir admin) |
| **2.3 Diagramme d'activité global** | navigation réelle de l'application Streamlit |
| **2.4 Diagramme d'activité administrateur** | gestion des utilisateurs, historique, logs (avec A pour « gestion des données ») |
| **Sécurité et gestion des utilisateurs (F6)** | bcrypt (pourquoi on ne stocke jamais un mot de passe en clair), token, 401/403, premier admin |
| **Interface utilisateur (Streamlit)** | architecture du frontend (`api_client`, `auth_guard`, `selecteurs`), captures d'écran de l'accueil et des menus |
| **Diagramme SQL** | envoyer à A les tables `utilisateur` et `journal` |
| **Diagramme de classes** | envoyer à A tes classes (`Utilisateur`, DAO, services, controllers) en Mermaid |

---

## Checklist

- [ ] S1 : `controller/auth.py` provisoire — **prévenir le groupe**
- [ ] S1 : squelette Streamlit qui tourne sur le port 8000 + `api_client` + `selecteurs` — **prévenir le groupe**
- [ ] S2 : tables, DAO, services (bcrypt, token)
- [ ] S3 : endpoints comptes + admin + journal
- [ ] S3 : vraies gardes `utilisateur_connecte` / `admin_requis`
- [ ] S3 : script du premier admin
- [ ] S4 : pages connexion, création de compte, déconnexion, admin utilisateurs, historique
- [ ] S4-S5 : tests, vérification de toutes les pages avec connexion
- [ ] Rapport : cas d'utilisation, activité globale et admin, sécurité, interface, tables et classes envoyées à A

## Tu dépends de / tu fournis à

- **Tu fournis** : gardes d'authentification (tout le monde, S1), squelette Streamlit + `selecteurs` (C, D, E, A), `JournalService` (A).
- **Tu dépends de A** : `GET /pays` et `GET /indicateurs/{code}/classif1` pour les sélecteurs. En attendant, tu peux mettre des listes écrites en dur.
