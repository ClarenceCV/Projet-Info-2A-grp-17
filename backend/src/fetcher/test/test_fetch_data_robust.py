from unittest.mock import patch

import pandas as pd

from config_import import PAYS_SUIVIS
from fetcher.data_processing import DataProcessing


def _code_pays(url: str) -> str:
    """Extrait le code ISO de l'url (…&ref_area=FRA -> 'FRA')."""
    return url.split("ref_area=")[-1]


def test_fetch_data_un_pays_en_erreur():
    """Un pays qui échoue est ignoré, les autres sont quand même renvoyés."""
    pays_en_panne = PAYS_SUIVIS[0]
    appels = []

    def faux_load_data(url):
        code = _code_pays(url)
        appels.append(code)
        if code == pays_en_panne:
            raise RuntimeError("502 Bad Gateway")
        return pd.DataFrame({"ref_area": [code], "obs_value": [1.0]})

    with patch("fetcher.data_processing.load_data", side_effect=faux_load_data), \
         patch("fetcher.data_processing.time.sleep") as faux_sleep:
        df = DataProcessing().fetch_data("INDICATEUR_TEST")

    pays_recus = set(df["ref_area"])
    assert pays_en_panne not in pays_recus
    assert pays_recus == set(PAYS_SUIVIS) - {pays_en_panne}
    # le pays en panne a bien été réessayé (nb_try = 2 dans ton code)
    assert appels.count(pays_en_panne) == 2
    faux_sleep.assert_called()   # on a attendu entre deux essais


def test_fetch_data_erreur_temporaire_puis_succes():
    """Un pays qui échoue une fois puis réussit est bien récupéré."""
    pays_instable = PAYS_SUIVIS[0]
    essais = {"n": 0}

    def faux_load_data(url):
        code = _code_pays(url)
        if code == pays_instable:
            essais["n"] += 1
            if essais["n"] == 1:
                raise RuntimeError("502 Bad Gateway")
        return pd.DataFrame({"ref_area": [code], "obs_value": [1.0]})

    with patch("fetcher.data_processing.load_data", side_effect=faux_load_data), \
         patch("fetcher.data_processing.time.sleep"):
        df = DataProcessing().fetch_data("INDICATEUR_TEST")

    assert set(df["ref_area"]) == set(PAYS_SUIVIS)