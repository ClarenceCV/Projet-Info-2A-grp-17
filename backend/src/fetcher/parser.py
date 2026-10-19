# Le fetcher a récupéré les données au format df
# Le parser sert à transformer ces df pour gérer les valeurs manquantes, reformater.. En sortie on doit avoir un df propre
# dont les colonnes sont parfaitement alignées avec nos business_object
# La fonction "mapper" transforme ensuite le df propre en objets python (Observation)

import pandas as pd

from business_object.indicateur import Indicateur
from business_object.observation import Observation
from business_object.pays import Pays
from business_object.profession import Profession

# Colonnes du CSV ILOSTAT à garder -> nom dans notre df propre
# (le fetcher doit utiliser type=both pour avoir à la fois ref_area (code) et ref_area.label (nom))
COLONNES_ILOSTAT = {
    "ref_area": "code_iso",
    "ref_area.label": "nom_pays",
    "source.label": "source",
    "sex.label": "sexe",
    "classif1.label": "classif1",
    "time": "periode",
    "obs_value": "valeur",
}

# Colonnes qui identifient une observation (= contrainte UNIQUE de la table observation)
CLE_OBSERVATION = ["code_iso", "sexe", "profession", "tranche_age", "periode"]

FORMAT_PERIODE = r"^\d{4}Q[1-4]$"


def retirer_prefixe(libelle):
    '''
    Retire le préfixe ajouté par ILOSTAT devant les libellés.
    ex : 'Sex: Female' -> 'Female' ; 'Age (Youth, adults): 15-64' -> '15-64'

    params:
        libelle: str | None
    '''
    if pd.isna(libelle):
        return None
    return libelle.split(": ", 1)[-1].strip()
