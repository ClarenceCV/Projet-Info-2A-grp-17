# Fiche D — Comparaison entre pays (F4) et carte du monde (FO2)

> **Ton rôle en une phrase** : tu codes la comparaison d'un indicateur entre plusieurs pays (classement, valeurs les plus hautes et les plus basses), puis son affichage sur une carte du monde.
> En le faisant, tu vas toucher **chaque couche** de l'application : c'est le meilleur moyen de comprendre tout le projet.

**Le sujet** :
- **F4** : *« Pour la période la plus récente disponible, permettre à l'utilisateur de comparer un indicateur (ex : taux d'activité par sexe et âge) entre plusieurs pays sélectionnés, et d'identifier les pays avec les valeurs les plus hautes/basses. »*
- **FO2 (optionnel)** : *« Visualiser un indicateur sur une carte du monde (choroplèthe), avec un code couleur selon la valeur par pays. »*

Lis d'abord [00_commun.md](00_commun.md).

---

## Tes fichiers

| Fichier | Statut |
|---|---|
| `backend/src/service/comparaison_pays_service.py` | à créer — **le cœur de ton travail** |
| `backend/src/schema/comparaison_pays_model.py` | à créer |
| `backend/src/controller/comparaison_pays_controller.py` | à créer |
| `backend/tests/test_service/test_comparaison_pays_service.py` | à créer |
| `frontend/pages/comparaison_pays.py`, `frontend/pages/carte.py` | à remplir (créées vides par B) |
| `backend/src/main.py` | **une ligne** à ajouter (partagé) |

Tu n'as **pas** besoin de toucher à la base ni au DAO : `ObservationDAO.lire` fait déjà tout ce qu'il te faut.

---

## Étape 0 — Comprendre l'existant (semaine 1, 1 à 2 jours)

### 0.a Faire tourner le projet
Suis la section 3 de la fiche commune jusqu'à obtenir **30.766** dans `/docs`. Si tu bloques, demande à A ou B.

### 0.b Suivre une requête dans le code
Ouvre ces fichiers dans l'ordre et lis-les en entier, en suivant la requête `GET /observations` :

| # | Fichier | Ce qu'il faut comprendre |
|---|---|---|
| 1 | `main.py` | `app.include_router(...)` : comment un controller est branché sous un préfixe |
| 2 | `controller/observation_controller.py` | paramètres d'URL (`Query`), liste de pays (`pays=FRA&pays=ESP`), `HTTPException(404)`, `df.to_dict(orient="records")` |
| 3 | `service/observation_service.py` | le service appelle le DAO (ici sans calcul : **ton** service fera les calculs) |
| 4 | `dao/observation_dao.py` → `lire` | la requête SQL avec `JOIN`, le `WHERE` construit selon les filtres, le DataFrame renvoyé |
| 5 | `schema/observation_model.py` | le format JSON d'une observation (Pydantic) |
| 6 | `data/init_db.sql` | les 3 tables et la clé primaire d'`observation` |

### 0.c Exercices de vérification
1. Dans `/docs`, compare à la main le **taux d'emploi total (15+) au 2024Q4** de la France, de l'Allemagne, de l'Espagne et de l'Italie. Quel pays est le plus haut ?
2. En console, depuis `backend/src` :
   ```bash
   uv run python -c "
   import dotenv; dotenv.load_dotenv()
   from dao.observation_dao import ObservationDAO
   df = ObservationDAO().lire('EMP_5WAP_SEX_AGE_RT_Q', ['FRA', 'DEU', 'ESP', 'ITA'], sexe='Total', classif1='15+')
   print(df.groupby('code_iso')['periode'].max())
   "
   ```
   Tous les pays ont-ils la **même** dernière période ? (La réponse oriente un choix de conception, voir étape 2.)
3. Explique à l'oral le chemin d'une requête, de l'URL jusqu'à la base et retour.

✅ **Tu es prêt quand** tu sais dire quel fichier modifier pour : ajouter un paramètre d'URL, changer une requête SQL, changer le format du JSON.

---

## Étape 1 — Le contrat de ton endpoint (semaine 1)

Écris ta section dans `doc/api.md`. Proposition :

```
GET /analyses/comparaison-pays
Paramètres :
  indicateur  (obligatoire) ex : EMP_5WAP_SEX_AGE_RT_Q
  classif1    (obligatoire) ex : 15+  (liste : GET /indicateurs/{code}/classif1)
  pays        (répétable, facultatif : si absent → tous les pays de la base — utile pour la carte)
  sexe        (défaut : Total)
  top         (défaut : 3) nombre de pays dans « plus hauts » et « plus bas »
Réponse 200 :
  {
    "periode_reference": "2024Q4",
    "classement": [{"rang": 1, "code_iso": "DEU", "nom_pays": "Germany", "periode": "2024Q4", "valeur": 61.2, "unite": "%"}, ...],
    "plus_hauts": [...les `top` premiers...],
    "plus_bas":   [...les `top` derniers...]
  }
Erreurs : 404 indicateur inconnu
```

---

## Étape 2 — Le service (semaine 2) : le cœur

`service/comparaison_pays_service.py`. C'est du **pandas** : pas de SQL, pas de FastAPI.

### Le choix de conception à faire : « la période la plus récente disponible »
Tous les pays ne publient pas au même rythme : la France peut avoir 2024Q4 alors qu'un autre pays s'arrête à 2024Q2. Deux options :
- **(a)** la période la plus récente **commune** : on prend la plus récente, et les pays qui ne l'ont pas sont exclus ;
- **(b)** la dernière période **de chaque pays** : tous les pays sont comparés, mais pas forcément à la même date (on l'affiche dans une colonne `periode`).

Choisis, explique ton choix dans le rapport, et affiche toujours la période de chaque pays pour que l'utilisateur ne soit pas trompé. (L'option (b) est plus utile pour la carte : moins de pays « vides ».)

### L'algorithme (option b)
1. Lire les observations avec `ObservationDAO().lire(...)`.
2. **Une seule source par pays et par période** : trier puis `drop_duplicates(["code_iso", "periode"], keep="first")`.
3. Garder la **dernière période de chaque pays** : trier par période puis `groupby("code_iso").tail(1)`.
4. Trier par valeur décroissante et ajouter une colonne `rang` (1, 2, 3…).
5. `plus_hauts` = les `top` premières lignes, `plus_bas` = les `top` dernières.
6. `periode_reference` = la période la plus récente du résultat.

### Squelette
```python
# Logique métier de la fonctionnalité F4 : comparaison d'un indicateur entre pays

import pandas as pd

from dao.observation_dao import ObservationDAO


class ComparaisonPaysService:
    """
    Compare un indicateur entre plusieurs pays, à la période la plus récente disponible (F4).
    """

    def comparer_pays(
        self,
        code_indicateur: str,
        classif1: str,
        pays: list[str] | None = None,
        sexe: str = "Total",
        top: int = 3,
    ) -> dict:
        """
        Returns:
            dict: {"periode_reference": str,
                   "classement": pd.DataFrame (rang, code_iso, nom_pays, periode, valeur, unite),
                   "plus_hauts": pd.DataFrame, "plus_bas": pd.DataFrame}
        """
        df = ObservationDAO().lire(code_indicateur, pays, sexe=sexe, classif1=classif1)
        # 1. une source par pays et période
        # 2. dernière période de chaque pays
        # 3. tri décroissant + rang
        # 4. plus hauts / plus bas
        ...
```

Teste en console au fur et à mesure (comme l'exercice 0.c), sur la vraie base.

---

## Étape 3 — Les tests (semaine 2)

`backend/tests/test_service/test_comparaison_pays_service.py`. On remplace le DAO par un **faux** (`patch.object`) qui renvoie un petit DataFrame écrit à la main.

```python
from unittest.mock import patch

import pandas as pd

from dao.observation_dao import ObservationDAO
from service.comparaison_pays_service import ComparaisonPaysService


def faux_df():
    """3 pays ; l'Espagne s'arrête un trimestre plus tôt"""
    return pd.DataFrame({
        "code_iso": ["FRA", "FRA", "DEU", "DEU", "ESP"],
        "nom_pays": ["France", "France", "Germany", "Germany", "Spain"],
        "source": ["LFS"] * 5,
        "periode": ["2024Q3", "2024Q4", "2024Q3", "2024Q4", "2024Q3"],
        "valeur": [50.0, 52.0, 60.0, 61.0, 45.0],
        "unite": ["%"] * 5,
    })


def test_classement_par_valeur_decroissante():
    # GIVEN
    with patch.object(ObservationDAO, "lire", return_value=faux_df()):
        # WHEN
        res = ComparaisonPaysService().comparer_pays("X", classif1="15+", top=1)
    # THEN
    assert list(res["classement"]["code_iso"]) == ["DEU", "FRA", "ESP"]
    assert list(res["plus_hauts"]["code_iso"]) == ["DEU"]
    assert list(res["plus_bas"]["code_iso"]) == ["ESP"]
```

Tests à écrire au minimum :
- [ ] le classement est trié par valeur décroissante, avec les bons rangs ;
- [ ] on garde bien la **dernière** période de chaque pays (FRA → 52.0, pas 50.0) ;
- [ ] plus hauts / plus bas corrects, y compris si `top` est plus grand que le nombre de pays ;
- [ ] deux sources pour une même période : une seule ligne gardée ;
- [ ] DAO qui renvoie un DataFrame vide : pas d'erreur.

Lancer : `uv run pytest` depuis la racine.

---

## Étape 4 — Schéma et endpoint (semaine 3)

En **copiant et adaptant** `observation_model.py` et `observation_controller.py`.

### Schéma `schema/comparaison_pays_model.py`
Deux modèles **imbriqués** — nouveauté par rapport à l'existant :
```python
class PaysClasseModel(BaseModel):
    rang: int
    code_iso: str
    nom_pays: str
    periode: str
    valeur: float
    unite: str


class ComparaisonPaysModel(BaseModel):
    periode_reference: str | None
    classement: list[PaysClasseModel]
    plus_hauts: list[PaysClasseModel]
    plus_bas: list[PaysClasseModel]
```

### Controller `controller/comparaison_pays_controller.py`
- `@router.get("/comparaison-pays", response_model=ComparaisonPaysModel)`.
- Paramètres avec `Query(...)` ; `top: int = Query(3, ge=1, le=50)`.
- 404 si l'indicateur n'existe pas (copier la vérification de `observation_controller.py`).
- Chaque DataFrame du résultat → `df.to_dict(orient="records")`.
- Plus tard (semaine 4), protéger avec `utilisateur=Depends(utilisateur_connecte)` (fourni par B).

### Brancher dans `main.py` (une ligne)
```python
app.include_router(comparaison_pays_controller.router, prefix="/analyses", tags=["Analyses"])
```

✅ Test dans `/docs` : `indicateur=EMP_5WAP_SEX_AGE_RT_Q`, `classif1=15+`, sans pays → les 4 pays classés.

---

## Étape 5 — Les pages Streamlit (semaine 4)

### `frontend/pages/comparaison_pays.py`
Réutilise **les sélecteurs** et **le client API** de B (`utils/selecteurs.py`, `utils/api_client.py`).
- Sélecteurs : indicateur, pays (plusieurs), classif1, sexe, top.
- Diagramme en **barres** horizontales du classement (`px.bar(..., orientation="h")`), en mettant en couleur les plus hauts et les plus bas.
- Deux encadrés « Valeurs les plus hautes » / « les plus basses » (`st.metric` ou `st.dataframe`).
- Afficher la période de chaque pays si elles diffèrent.

### `frontend/pages/carte.py` — FO2 (à commencer quand F4 marche)
**Pas besoin de nouvel endpoint** : la carte, c'est la comparaison de **tous** les pays, affichée autrement.
```python
donnees = get("/analyses/comparaison-pays", {"indicateur": indicateur, "classif1": classif1, "sexe": sexe})
df = pd.DataFrame(donnees["classement"])
fig = px.choropleth(df, locations="code_iso", color="valeur", hover_name="nom_pays",
                    color_continuous_scale="Viridis")      # code_iso = code ISO à 3 lettres : Plotly le reconnaît
st.plotly_chart(fig)
```
⚠️ Avec seulement 4 pays, la carte est presque vide : vois avec **A** pour élargir `PAYS_SUIVIS` (par exemple tous les pays de l'UE + d'autres continents) et relancer l'import.

---

## Étape 6 — Rapport final : tes parties

| Partie | Contenu |
|---|---|
| **Fonctionnalité F4** | le calcul, **ton choix** pour « la période la plus récente disponible » (a ou b) et pourquoi, la gestion des sources multiples, une capture du graphique, un exemple commenté (« l'Allemagne a le taux d'emploi le plus élevé… ») |
| **Fonctionnalité FO2** | la carte : comment elle réutilise F4, capture d'écran, limites (pays sans données) |
| **2.5 Diagramme d'activité utilisateur** | fournir à C les branches « Comparaison pays » et « Carte » |
| **Diagramme de classes** | envoyer à A tes classes (`ComparaisonPaysService`, modèles, controller) en Mermaid |

---

## Checklist

- [ ] S1 : projet lancé sur Onyxia (30.766), parcours du code compris, exercices 0.c faits
- [ ] S1 : contrat dans `doc/api.md`
- [ ] S2 : `ComparaisonPaysService.comparer_pays` testé en console, choix (a)/(b) fait
- [ ] S2 : tests (`uv run pytest` passe)
- [ ] S3 : schéma + endpoint, testé dans `/docs`
- [ ] S3 : liste de pays élargie avec A
- [ ] S4 : page comparaison (barres + extrêmes)
- [ ] S4 : page carte (FO2)
- [ ] S4 : endpoint protégé par `utilisateur_connecte`
- [ ] Rapport : F4, FO2, branches du diagramme d'activité, classes envoyées à A

## Tu dépends de / tu fournis à

- **Tu dépends de** : A (tests prêts, `/indicateurs/{code}/classif1`, pays élargis), B (squelette Streamlit, sélecteurs, `utilisateur_connecte`).
- **Tu fournis** : `ComparaisonPaysService` à E, qui l'utilisera dans le rapport PDF (FO3).
