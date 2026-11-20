"""
Tests du service des observations.
Le DAO est remplacé par un faux (patch.object) qui renvoie un petit DataFrame écrit à la main :
les tests ne dépendent pas de la base et on connaît le résultat attendu.

Lancement (depuis le dossier backend) :
     uv run pytest src/tests
"""

from unittest.mock import patch

import pandas as pd

from dao.observation_dao import ObservationDAO
from service.observation_service import ObservationService


def test_lister_renvoie_le_dataframe_du_dao():
    """
    Vérifie que `lister` renvoie tel quel le DataFrame fourni par le DAO
    (ici 2 lignes, pour la France et l'Allemagne), sans dépendre de la base
    de données.
    """
    # GIVEN : un faux DAO qui renvoie 2 lignes, sans base de données
    faux_df = pd.DataFrame({"code_iso": ["FRA", "DEU"], "valeur": [1.0, 2.0]})
    with patch.object(ObservationDAO, "lire", return_value=faux_df):
        # WHEN
        res = ObservationService().lister("EMP_5WAP_SEX_AGE_RT_Q", ["FRA", "DEU"])
    # THEN
    assert len(res) == 2
