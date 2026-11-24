"""
Outils de nettoyage des libellés ILOSTAT, utilisés par DataProcessing.parse_data
(le nettoyage complet du DataFrame brut est fait dans fetcher/data_processing.py)
"""

import pandas as pd

from utils.log_utils import log


@log
def retirer_prefixe(libelle: str | None) -> str | None:
    """
    Retire le préfixe ajouté par ILOSTAT devant les libellés.
    ex : 'Sex: Female' -> 'Female' ; 'Age (Youth, adults): 15-64' -> '15-64'

    Args:
        libelle (str | None): libellé ILOSTAT (None ou NaN si la valeur manque)

    Returns:
        str | None: le libellé sans son préfixe, ou None si la valeur manque
    """
    if pd.isna(libelle):
        return None
    return libelle.split(": ", 1)[-1].strip()
