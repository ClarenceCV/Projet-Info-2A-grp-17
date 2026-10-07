# Fiche E — Comparaison multi-indicateurs (F5) et rapport PDF (FO3)

> **Ton rôle en une phrase** : tu codes la comparaison de plusieurs indicateurs sur un même graphique, puis la génération automatique d'un rapport PDF.
> En le faisant, tu vas toucher **chaque couche** de l'application : c'est le meilleur moyen de comprendre tout le projet.

**Le sujet** :
- **F5** : *« Permettre la comparaison simultanée de l'évolution de plusieurs indicateurs (ex : emploi et population active) sur un même graphique. »*
- **FO3 (optionnel)** : *« Générer automatiquement un rapport d'analyse au format PDF contenant : les principaux indicateurs sélectionnés ; les graphiques d'évolution ; les comparaisons entre pays ; un résumé statistique (minimum, maximum, moyenne, évolution sur la période) ; une conclusion synthétique générée automatiquement. »*

Lis d'abord [00_commun.md](00_commun.md).

---

## Tes fichiers

| Fichier | Statut |
|---|---|
| `backend/src/business_object/selection.py` | à créer |
| `backend/src/service/multi_indicateurs_service.py` | à créer — **le cœur de F5** |
| `backend/src/service/rapport_service.py` | à créer (FO3) |
| `backend/src/schema/multi_indicateurs_model.py` | à créer |
| `backend/src/controller/multi_indicateurs_controller.py`, `controller/rapport_controller.py` | à créer |
| `backend/tests/test_service/test_multi_indicateurs_service.py`, `test_rapport_service.py` | à créer |
| `frontend/pages/multi_indicateurs.py`, `frontend/pages/rapport.py` | à remplir (créées vides par B) |
| `backend/src/main.py` | **une ligne par controller** à ajouter (partagé) |

Tu n'as **pas** besoin de toucher à la base ni au DAO : `ObservationDAO.lire` et `IndicateurDAO.trouver_par_code` font déjà tout ce qu'il te faut.

---

## Étape 0 — Comprendre l'existant (semaine 1, 1 à 2 jours)

### 0.a Faire tourner le projet
Suis la section 3 de la fiche commune jusqu'à obtenir **30.766** dans `/docs`. Si tu bloques, demande à A ou B.

### 0.b Suivre une requête dans le code
Ouvre ces fichiers dans l'ordre et lis-les en entier, en suivant la requête `GET /observations` :

| # | Fichier | Ce qu'il faut comprendre |
|---|---|---|
| 1 | `main.py` | `app.include_router(...)` : comment un controller est branché sous un préfixe |
| 2 | `controller/observation_controller.py` | paramètres d'URL (`Query`), `HTTPException(404)`, `df.to_dict(orient="records")` |
| 3 | `service/observation_service.py` | le service appelle le DAO (ici sans calcul : **ton** service fera les calculs) |
| 4 | `dao/observation_dao.py` → `lire` | la requête SQL avec `JOIN`, le `WHERE` construit selon les filtres, le DataFrame renvoyé |
| 5 | `business_object/indicateur.py` | la dataclass `Indicateur` (tu vas créer une dataclass `Selection` sur le même modèle) |
| 6 | `schema/observation_model.py` | le format JSON d'une observation (Pydantic) |

### 0.c Exercices de vérification
1. Dans `/docs`, récupère pour la France, sexe Total, les séries des **deux** indicateurs : emploi (`classif1=Total`, en milliers) et taux d'emploi (`classif1=15+`, en %). Pourquoi ne peut-on pas les tracer telles quelles sur le même axe ?
2. En console, depuis `backend/src` :
   ```bash
   uv run python -c "
   import dotenv; dotenv.load_dotenv()
   from dao.observation_dao import ObservationDAO
   a = ObservationDAO().lire('EMP_5EMP_SEX_OC2_NB_Q', ['FRA'], sexe='Total', classif1='Total')
   b = ObservationDAO().lire('EMP_5WAP_SEX_AGE_RT_Q', ['FRA'], sexe='Total', classif1='15+')
   print(a['periode'].min(), b['periode'].min())
   "
   ```
   Les deux séries commencent-elles à la même période ?
3. Explique à l'oral le chemin d'une requête, de l'URL jusqu'à la base et retour.

✅ **Tu es prêt quand** tu sais dire quel fichier modifier pour : ajouter un paramètre, changer une requête SQL, changer le format du JSON.

---

## Étape 1 — Le contrat de ton endpoint (semaine 1, 15 minutes)

Voici ce que ton endpoint recevra et renverra. **Lis-le simplement** : B s'en sert pour préparer ta page Streamlit.
Si en codant tu veux changer un nom de paramètre ou de champ, pas de souci, mais **préviens B**.

**Nouveauté** : chaque indicateur a **ses propres filtres** (emploi → `classif1=Total` ; taux → `classif1=15+`). Avec de simples paramètres d'URL, ce serait illisible. On envoie donc une **liste de sélections dans le corps de la requête** (JSON) avec `POST`.

Le contrat :

```
POST /analyses/multi-indicateurs
Corps (JSON) : une liste de sélections (2 au minimum)
  [
    {"indicateur": "EMP_5EMP_SEX_OC2_NB_Q", "pays": "FRA", "sexe": "Total", "classif1": "Total"},
    {"indicateur": "EMP_5WAP_SEX_AGE_RT_Q", "pays": "FRA", "sexe": "Total", "classif1": "15+"}
  ]
Réponse 200 : une ligne par série et par période
  [{"serie": "Emploi par sexe et profession — France — Total — Total", "indicateur": "EMP_5EMP_SEX_OC2_NB_Q",
    "periode": "2024Q4", "valeur": 28933.2, "unite": "milliers", "valeur_base100": 101.3}, ...]
Erreurs : 404 indicateur inconnu ; 400 fréquences différentes (trimestriel + annuel)
```

---

## Étape 2 — F5 : le service (semaine 2) : le cœur

### 2.a La dataclass `Selection` (`business_object/selection.py`)
Sur le modèle de `Indicateur` :
```python
@dataclass(frozen=True)
class Selection:
    """Un indicateur + ses filtres : une courbe du graphique multi-indicateurs."""
    indicateur: str
    pays: str
    classif1: str
    sexe: str = "Total"
```

### 2.b La base 100 : l'idée
Les indicateurs n'ont pas la même unité (milliers vs %) : impossible de les comparer sur le même axe.
On transforme chaque série en **indice base 100** : la valeur de la première période vaut 100, les suivantes sont exprimées par rapport à elle.
Exemple : 50 → 51 → 53 devient 100 → 102 → 106. On lit alors directement « +6 % depuis le début », quelle que soit l'unité.

⚠️ Les séries doivent partir de la **même** période (sinon une courbe « commence à 100 » en 2020, l'autre en 2022 : la comparaison est fausse). On prend la **première période commune** à toutes les séries.

### 2.c L'algorithme
1. Pour chaque `Selection` :
   - récupérer l'indicateur (`IndicateurDAO().trouver_par_code`) → `ValueError` s'il n'existe pas ;
   - lire ses observations (`ObservationDAO().lire(indicateur, [pays], sexe=..., classif1=...)`) ;
   - une seule source par période (`drop_duplicates(["periode"])`) ;
   - ajouter une colonne `serie` (un nom lisible : libellé — pays — sexe — classif1).
2. Vérifier que tous les indicateurs ont la **même fréquence** (`Indicateur.frequence`), sinon `ValueError`.
3. Concaténer (`pd.concat`).
4. Première période commune : `debut = df.groupby("serie")["periode"].min().max()`, puis garder `periode >= debut`.
5. Trier par période, puis `valeur_base100 = valeur / première valeur de la série * 100`
   → `df.groupby("serie")["valeur"].transform("first")`.

### Squelette
```python
# Logique métier de la fonctionnalité F5 : comparaison de plusieurs indicateurs sur un même graphique

import pandas as pd

from business_object.selection import Selection
from dao.indicateur_dao import IndicateurDAO
from dao.observation_dao import ObservationDAO


class MultiIndicateursService:
    """
    Compare l'évolution de plusieurs indicateurs, ramenés en base 100 (F5).
    """

    def comparer(self, selections: list[Selection]) -> pd.DataFrame:
        """
        Returns:
            pd.DataFrame: colonnes serie, indicateur, periode, valeur, unite, valeur_base100

        Raises:
            ValueError: indicateur inconnu, ou fréquences différentes
        """
        ...
```

---

## Étape 3 — F5 : les tests (semaine 2)

Le service utilise **deux** DAO : il faut simuler les deux. `side_effect` permet de renvoyer une valeur différente à chaque appel.

```python
from unittest.mock import patch

import pandas as pd

from business_object.indicateur import Indicateur
from business_object.selection import Selection
from dao.indicateur_dao import IndicateurDAO
from dao.observation_dao import ObservationDAO
from service.multi_indicateurs_service import MultiIndicateursService

EMPLOI = Indicateur("A", "Emploi", "milliers", "Q")
TAUX = Indicateur("B", "Taux", "%", "Q")


def serie(periodes, valeurs, unite):
    return pd.DataFrame({"code_iso": "FRA", "nom_pays": "France", "source": "LFS",
                         "periode": periodes, "valeur": valeurs, "unite": unite})


def test_base100_sur_premiere_periode_commune():
    # GIVEN : la série A commence en 2024Q1, la série B en 2024Q2
    a = serie(["2024Q1", "2024Q2", "2024Q3"], [10.0, 20.0, 30.0], "milliers")
    b = serie(["2024Q2", "2024Q3"], [50.0, 55.0], "%")
    selections = [Selection("A", "FRA", "Total"), Selection("B", "FRA", "15+")]
    with patch.object(IndicateurDAO, "trouver_par_code", side_effect=[EMPLOI, TAUX]), \
         patch.object(ObservationDAO, "lire", side_effect=[a, b]):
        # WHEN
        res = MultiIndicateursService().comparer(selections)
    # THEN : tout commence en 2024Q2, et chaque série y vaut 100
    assert res["periode"].min() == "2024Q2"
    assert list(res[res["periode"] == "2024Q2"]["valeur_base100"]) == [100.0, 100.0]
```

Tests à écrire au minimum :
- [ ] base 100 correcte (100 à la première période commune, valeurs suivantes justes : A en 2024Q3 → 150) ;
- [ ] les séries sont coupées à la première période commune ;
- [ ] fréquences différentes → `ValueError` (utiliser `pytest.raises`) ;
- [ ] indicateur inconnu → `ValueError`.

---

## Étape 4 — F5 : schéma et endpoint (semaine 3)

### Schémas `schema/multi_indicateurs_model.py`
```python
class SelectionModel(BaseModel):          # ce que le client ENVOIE (corps de la requête)
    indicateur: str
    pays: str
    classif1: str
    sexe: str = "Total"


class PointSerieModel(BaseModel):          # ce que l'API RENVOIE
    serie: str
    indicateur: str
    periode: str
    valeur: float
    unite: str
    valeur_base100: float
```

### Controller `controller/multi_indicateurs_controller.py`
```python
@router.post("/multi-indicateurs", response_model=list[PointSerieModel])
async def comparer_indicateurs(selections: list[SelectionModel]):
    ...
```
- Un paramètre de type **modèle Pydantic** (ou liste de modèles) est lu dans le **corps JSON** de la requête : c'est la nouveauté par rapport à `GET /observations`.
- Convertir chaque `SelectionModel` en `Selection` : `Selection(**s.model_dump())`.
- Moins de 2 sélections → `HTTPException(400)`.
- `ValueError` du service → `HTTPException(400, detail=str(e))` (ou 404 si indicateur inconnu).
- Brancher dans `main.py` : `app.include_router(multi_indicateurs_controller.router, prefix="/analyses", tags=["Analyses"])`.
- Plus tard (semaine 4), protéger avec `utilisateur=Depends(utilisateur_connecte)` (fourni par B).

✅ Test dans `/docs` : `POST /analyses/multi-indicateurs` → **Try it out** → coller le JSON du contrat → deux séries qui valent 100 à la même période.

---

## Étape 5 — F5 : la page Streamlit (semaine 4)

`frontend/pages/multi_indicateurs.py`, avec les sélecteurs et le client API de B.
- Permettre de construire 2 à 4 sélections (une colonne `st.columns` par sélection : indicateur, pays, classif1, sexe).
- Appeler `post("/analyses/multi-indicateurs", json=[...])`.
- Graphique : `px.line(df, x="periode", y="valeur_base100", color="serie", markers=True)` + une ligne horizontale à 100.
- Option : un bouton pour afficher les valeurs brutes (deux axes Y avec `plotly.graph_objects`).

---

## Étape 6 — FO3 : le rapport PDF (semaines 4 et 5, quand F5 marche)

Le rapport **réutilise les services des autres** : c'est la fonctionnalité qui assemble tout.

| Contenu demandé par le sujet | D'où ça vient |
|---|---|
| indicateurs sélectionnés | `IndicateurDAO.trouver_par_code` |
| graphiques d'évolution | `EvolutionService` (**C**) |
| comparaisons entre pays | `ComparaisonPaysService` (**D**) |
| résumé statistique (min, max, moyenne, évolution sur la période) | à calculer toi-même sur le DataFrame d'évolution |
| conclusion automatique | phrases construites à partir des chiffres (« Entre 2023Q1 et 2024Q4, le taux d'emploi en France a augmenté de 1,2 point. L'Allemagne a la valeur la plus élevée… ») |

### Outils
- `uv add fpdf2 matplotlib`
- **matplotlib** pour dessiner les graphiques en image (enregistrés dans un `io.BytesIO`, pas sur le disque) ;
- **fpdf2** pour assembler le PDF (titres, texte, tableaux, images).

### Le service `service/rapport_service.py`
```python
class RapportService:
    def generer(self, code_indicateur: str, pays: list[str], classif1: str,
                sexe: str = "Total", n_periodes: int = 8) -> bytes:
        """Renvoie le contenu du fichier PDF."""
        evolution = EvolutionService().evolution(code_indicateur, pays, classif1, sexe, n_periodes)
        comparaison = ComparaisonPaysService().comparer_pays(code_indicateur, classif1, pays, sexe)
        resume = self.resume_statistique(evolution)        # à tester séparément
        conclusion = self.conclusion(evolution, comparaison)  # à tester séparément
        ...  # graphiques matplotlib + assemblage fpdf2
```
Découpe en petites méthodes (`resume_statistique`, `conclusion`) : elles se testent facilement avec un DataFrame écrit à la main, contrairement au PDF lui-même.

### L'endpoint `controller/rapport_controller.py`
```python
from fastapi.responses import Response

@router.get("/rapport")
async def generer_rapport(indicateur: str, pays: list[str] = Query(...), classif1: str = Query(...)):
    pdf = RapportService().generer(indicateur, pays, classif1)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=rapport_laborscope.pdf"})
```
Brancher dans `main.py` (`tags=["Rapport"]`).

### La page `frontend/pages/rapport.py`
Sélecteurs, puis `st.download_button("Télécharger le rapport", data=<octets du PDF>, file_name="rapport.pdf")`. Le client API de B renvoie du JSON : il faudra peut-être lui ajouter une fonction qui renvoie les octets bruts (voir avec B).

### Tests FO3
- [ ] `resume_statistique` : min, max, moyenne et évolution justes sur un petit DataFrame ;
- [ ] `conclusion` : la phrase mentionne le bon pays le plus haut ;
- [ ] `generer` (avec les services de C et D simulés) renvoie des octets qui commencent par `b"%PDF"`.

---

## Étape 7 — Rapport final : tes parties

| Partie | Contenu |
|---|---|
| **Fonctionnalité F5** | la base 100 expliquée simplement, la première période commune, le contrôle de fréquence, une capture du graphique, un exemple commenté |
| **Fonctionnalité FO3** | ce que contient le rapport, comment il réutilise les autres services, comment la conclusion est générée, limites |
| **Annexe** | un exemple de rapport PDF généré |
| **2.5 Diagramme d'activité utilisateur** | fournir à C les branches « Multi-indicateurs » et « Rapport » |
| **Diagramme de classes** | envoyer à A tes classes (`Selection`, `MultiIndicateursService`, `RapportService`, modèles, controllers) en Mermaid |

---

## Checklist

- [ ] S1 : projet lancé sur Onyxia (30.766), parcours du code compris, exercices 0.c faits
- [ ] S1 : contrat de l'étape 1 lu (et B prévenu si changement)
- [ ] S2 : `Selection` + `MultiIndicateursService.comparer` testé en console
- [ ] S2 : tests F5 (`uv run pytest` passe)
- [ ] S3 : schémas + endpoint `POST`, testé dans `/docs`
- [ ] S4 : page Streamlit multi-indicateurs
- [ ] S4-S5 : rapport PDF (service, tests, endpoint, page de téléchargement)
- [ ] S4 : endpoints protégés par `utilisateur_connecte`
- [ ] Rapport : F5, FO3, exemple en annexe, branches du diagramme d'activité, classes envoyées à A

## Tu dépends de / tu fournis à

- **Tu dépends de** : A (tests prêts, `/indicateurs/{code}/classif1`), B (squelette Streamlit, sélecteurs, `utilisateur_connecte`), **C et D** pour FO3 (`EvolutionService`, `ComparaisonPaysService`) — d'où FO3 en fin de planning.
