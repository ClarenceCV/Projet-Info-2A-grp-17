# Fiche C — Évolution d'un indicateur (F3)

> **Ton rôle en une phrase** : tu codes la fonctionnalité F3 de bout en bout — calculer l'évolution d'un indicateur sur les N derniers trimestres et l'afficher en graphique.
> En le faisant, tu vas toucher **chaque couche** de l'application : c'est le meilleur moyen de comprendre tout le projet.

**Le sujet (F3)** : *« Permettre le calcul de l'évolution d'un indicateur donné (ex : emploi par profession) sur une période définie (par exemple : les 8 derniers trimestres) et afficher les résultats sous forme de graphiques. »*

Lis d'abord [00_commun.md](00_commun.md).

---

## Tes fichiers

| Fichier | Statut |
|---|---|
| `backend/src/service/evolution_service.py` | à créer — **le cœur de ton travail** |
| `backend/src/schema/evolution_model.py` | à créer |
| `backend/src/controller/evolution_controller.py` | à créer |
| `backend/tests/test_service/test_evolution_service.py` | à créer |
| `frontend/pages/evolution.py` | à remplir (créée vide par B) |
| `backend/src/main.py` | **une ligne** à ajouter (partagé) |

Tu n'as **pas** besoin de toucher à la base ni au DAO : `ObservationDAO.lire` fait déjà tout ce qu'il te faut.

---

## Étape 0 — Comprendre l'existant (semaine 1, 1 à 2 jours)

### 0.a Faire tourner le projet
Suis la section 3 de la fiche commune jusqu'à obtenir **30.766** dans `/docs`. Si tu bloques, demande à A ou B : c'est normal, et c'est leur rôle de t'aider.

### 0.b Suivre une requête dans le code
Ouvre ces fichiers dans l'ordre et lis-les en entier, en suivant la requête `GET /observations` :

| # | Fichier | Ce qu'il faut comprendre |
|---|---|---|
| 1 | `main.py` | `app.include_router(...)` : comment un controller est branché sous un préfixe (`/observations`) |
| 2 | `controller/observation_controller.py` | les paramètres de la fonction deviennent des **paramètres d'URL** ; `HTTPException(404)` ; conversion `df.to_dict(orient="records")` |
| 3 | `service/observation_service.py` | le service appelle le DAO (ici sans calcul : c'est **ton** service qui fera des calculs) |
| 4 | `dao/observation_dao.py` → `lire` | la requête SQL avec `JOIN`, le `WHERE` construit selon les filtres, le DataFrame renvoyé |
| 5 | `schema/observation_model.py` | le format JSON d'une observation (Pydantic) |
| 6 | `data/init_db.sql` | les 3 tables et la clé primaire d'`observation` |

### 0.c Exercices de vérification
1. Dans `/docs`, trouve le **taux d'emploi des hommes de 25 ans et plus en Espagne au 2024Q3**.
2. Dans le terminal, depuis `backend/src`, affiche le DataFrame renvoyé par le DAO :
   ```bash
   uv run python -c "
   import dotenv; dotenv.load_dotenv()
   from dao.observation_dao import ObservationDAO
   df = ObservationDAO().lire('EMP_5WAP_SEX_AGE_RT_Q', ['FRA'], sexe='Total', classif1='15+')
   print(df[['code_iso', 'periode', 'source', 'valeur']])
   "
   ```
   Combien de périodes y a-t-il ? Y a-t-il plusieurs sources pour une même période ?
3. Explique à l'oral (à toi-même ou à quelqu'un) le chemin d'une requête, de l'URL jusqu'à la base et retour.

✅ **Tu es prêt quand** tu sais dire quel fichier modifier pour : ajouter un paramètre d'URL, changer une requête SQL, changer le format du JSON.

---

## Étape 1 — Le contrat de ton endpoint (semaine 1, 15 minutes)

Voici ce que ton endpoint recevra et renverra. **Lis-le simplement** : B s'en sert pour préparer ta page Streamlit.
Si en codant tu veux changer un nom de paramètre ou de champ, pas de souci, mais **préviens B**.

```
GET /analyses/evolution
Paramètres :
  indicateur  (obligatoire) ex : EMP_5WAP_SEX_AGE_RT_Q
  pays        (obligatoire, répétable) ex : pays=FRA&pays=ESP
  classif1    (obligatoire) ex : 15+  (profession ou tranche d'âge ; liste : GET /indicateurs/{code}/classif1)
  sexe        (défaut : Total)
  n_periodes  (défaut : 8, entre 1 et 40)
Réponse 200 : une ligne par pays et par période
  [{"code_iso": "FRA", "nom_pays": "France", "periode": "2024Q4", "valeur": 52.07,
    "unite": "%", "variation_abs": 0.31, "variation_pct": 0.6}, ...]
Erreurs : 404 indicateur inconnu
```

Pourquoi `classif1` est obligatoire : sans lui, on mélangerait toutes les professions (ou toutes les tranches d'âge) dans une même courbe.

---

## Étape 2 — Le service (semaine 2) : le cœur

`service/evolution_service.py`. C'est du **pandas** : pas de SQL, pas de FastAPI.

### L'algorithme
1. Lire les observations avec `ObservationDAO().lire(...)` → DataFrame.
2. **Une seule source par pays et par période** (sinon deux points pour la même date) : trier puis `drop_duplicates(["code_iso", "periode"], keep="first")`.
3. Trier par pays puis période.
4. Calculer, **pour chaque pays séparément** (`groupby("code_iso")`) :
   - `variation_abs` = valeur − valeur précédente → `.diff()`
   - `variation_pct` = variation en % → `.pct_change() * 100`
5. Garder les **N dernières périodes** de chaque pays → `.groupby("code_iso").tail(n_periodes)`.

⚠️ L'ordre 4 puis 5 est important : si on coupait d'abord, la première période gardée n'aurait pas de variation.

### Squelette
```python
# Logique métier de la fonctionnalité F3 : évolution d'un indicateur sur les N dernières périodes

import pandas as pd

from dao.observation_dao import ObservationDAO


class EvolutionService:
    """
    Calcule l'évolution d'un indicateur dans le temps (F3).
    """

    def evolution(
        self,
        code_indicateur: str,
        pays: list[str],
        classif1: str,
        sexe: str = "Total",
        n_periodes: int = 8,
    ) -> pd.DataFrame:
        """
        Évolution d'un indicateur sur les n dernières périodes, pour chaque pays.

        Returns:
            pd.DataFrame: colonnes code_iso, nom_pays, periode, valeur, unite,
                          variation_abs, variation_pct (une ligne par pays et période)
        """
        df = ObservationDAO().lire(code_indicateur, pays, sexe=sexe, classif1=classif1)

        # 1. une seule source par pays et par période
        # 2. tri par pays puis période
        # 3. variations par pays (groupby + diff / pct_change)
        # 4. n dernières périodes par pays (groupby + tail)
        ...
        return df[["code_iso", "nom_pays", "periode", "valeur", "unite", "variation_abs", "variation_pct"]]
```

Teste en console au fur et à mesure (comme l'exercice 0.c), sur la vraie base.

---

## Étape 3 — Les tests (semaine 2)

`backend/tests/test_service/test_evolution_service.py`. On remplace le DAO par un **faux** (`patch.object`) qui renvoie un petit DataFrame écrit à la main : le test ne dépend ni de la base ni d'ILOSTAT, et on connaît le résultat attendu.

```python
from unittest.mock import patch

import pandas as pd

from dao.observation_dao import ObservationDAO
from service.evolution_service import EvolutionService


def faux_df():
    """3 périodes pour la France"""
    return pd.DataFrame({
        "code_iso": ["FRA", "FRA", "FRA"],
        "nom_pays": ["France"] * 3,
        "source": ["LFS"] * 3,
        "periode": ["2024Q1", "2024Q2", "2024Q3"],
        "valeur": [50.0, 51.0, 53.0],
        "unite": ["%"] * 3,
    })


def test_evolution_calcule_les_variations():
    # GIVEN
    with patch.object(ObservationDAO, "lire", return_value=faux_df()):
        # WHEN
        res = EvolutionService().evolution("X", ["FRA"], classif1="15+", n_periodes=8)
    # THEN
    assert list(res["variation_abs"])[1:] == [1.0, 2.0]


def test_evolution_garde_les_n_dernieres_periodes():
    ...  # n_periodes=2 → seulement 2024Q2 et 2024Q3, et 2024Q2 a bien une variation (1.0)
```

Tests à écrire au minimum :
- [ ] les variations absolues et en % sont justes ;
- [ ] seules les N dernières périodes sont gardées, **avec** leur variation ;
- [ ] deux pays : les variations ne « débordent » pas d'un pays à l'autre ;
- [ ] deux sources pour une même période : une seule ligne gardée ;
- [ ] DAO qui renvoie un DataFrame vide : pas d'erreur, résultat vide.

Lancer : `uv run pytest` depuis la racine.

---

## Étape 4 — Schéma et endpoint (semaine 3)

En **copiant et adaptant** `observation_model.py` et `observation_controller.py`.

### Schéma `schema/evolution_model.py`
```python
class EvolutionModel(BaseModel):
    code_iso: str
    nom_pays: str
    periode: str
    valeur: float
    unite: str
    variation_abs: float | None = None   # None pour la première période (pas de précédente)
    variation_pct: float | None = None
```

### Controller `controller/evolution_controller.py`
- `router = APIRouter()` puis `@router.get("/evolution", response_model=list[EvolutionModel])`.
- Paramètres avec `Query(...)` comme dans `observation_controller.py` ; `n_periodes: int = Query(8, ge=1, le=40)`.
- 404 si l'indicateur n'existe pas (copier la vérification de `observation_controller.py`).
- ⚠️ **Piège** : la première variation de chaque pays vaut `NaN`, et **le JSON n'accepte pas `NaN`** (erreur 500). Avant `to_dict`, remplacer les `NaN` par `None` :
  ```python
  df = df.astype(object).where(df.notna(), None)
  ```
- Plus tard (semaine 4), protéger l'endpoint avec `utilisateur=Depends(utilisateur_connecte)` (fourni par B dans `controller/auth.py`).

### Brancher dans `main.py` (une ligne)
```python
app.include_router(evolution_controller.router, prefix="/analyses", tags=["Analyses"])
```

✅ Test dans `/docs` : `indicateur=EMP_5WAP_SEX_AGE_RT_Q`, `pays=FRA`, `pays=ESP`, `classif1=15+`, `n_periodes=8` → 16 lignes.

---

## Étape 5 — La page Streamlit (semaine 4)

`frontend/pages/evolution.py`, dans le squelette créé par B. Réutilise **ses sélecteurs** (`utils/selecteurs.py`) et **son client API** (`utils/api_client.py`) : ne recode pas de menus ni d'appels HTTP.

```python
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import get
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_pays, choisir_sexe

st.title("Évolution d'un indicateur")

indicateur = choisir_indicateur()
pays = choisir_pays(multiple=True)
classif1 = choisir_classif1(indicateur)
sexe = choisir_sexe()
n = st.slider("Nombre de trimestres", 2, 20, 8)

donnees = get("/analyses/evolution", {"indicateur": indicateur, "pays": pays,
                                      "classif1": classif1, "sexe": sexe, "n_periodes": n})
df = pd.DataFrame(donnees)
st.plotly_chart(px.line(df, x="periode", y="valeur", color="nom_pays", markers=True))
st.dataframe(df)   # tableau avec les variations
```

(Les noms exacts des fonctions de B peuvent varier : regarde son code.)

---

## Étape 6 — Rapport final : tes parties

| Partie | Contenu |
|---|---|
| **2.5 Diagramme d'activité utilisateur** — à refaire | Le diagramme actuel range « Comparaison entre pays » sous « Analyse temporelle » et n'a pas F3. Refais-le avec **5 entrées au même niveau** : Évolution (F3), Comparaison pays (F4), Carte (FO2), Multi-indicateurs (F5), Rapport (FO3). Coordonne-toi avec D et E pour leurs branches. |
| **2.6 Diagramme de séquence** — à refaire | Remplacer l'exemple « taux de chômage » (pas un de nos indicateurs) par **ta** fonctionnalité : Utilisateur → Streamlit → `GET /analyses/evolution` → `EvolutionService` → `ObservationDAO.lire` → PostgreSQL, et le retour (DataFrame → JSON → graphique). Tu connais ce chemin par cœur après l'étape 0. |
| **Fonctionnalité F3** | ce que fait la fonctionnalité, le calcul (variations, pourquoi on calcule avant de couper, une source par période), une capture du graphique, un exemple de résultat commenté |
| **Diagramme de classes** | envoyer à A tes classes (`EvolutionService`, `EvolutionModel`, controller) en Mermaid |

---

## Checklist

- [ ] S1 : projet lancé sur Onyxia (30.766), parcours du code compris, exercices 0.c faits
- [ ] S1 : contrat de l'étape 1 lu (et B prévenu si changement)
- [ ] S2 : `EvolutionService.evolution` testé en console
- [ ] S2 : tests (`uv run pytest` passe)
- [ ] S3 : schéma + endpoint, testé dans `/docs`
- [ ] S4 : page Streamlit avec graphique
- [ ] S4 : endpoint protégé par `utilisateur_connecte`
- [ ] Rapport : activité utilisateur, séquence, section F3, classes envoyées à A

## Tu dépends de / tu fournis à

- **Tu dépends de** : A (tests prêts, `/indicateurs/{code}/classif1`), B (squelette Streamlit, sélecteurs, `utilisateur_connecte`).
- **Tu fournis** : `EvolutionService` à E, qui l'utilisera dans le rapport PDF (FO3).
