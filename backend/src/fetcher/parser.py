# Outils de nettoyage des libellés ILOSTAT, utilisés par DataProcessing.parse_data
# (le nettoyage complet du DataFrame brut est fait dans fetcher/data_processing.py)

import pandas as pd


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
