# Tests de PaysDAO sur la vraie base (données de test 'ZZZ', supprimées après chaque test : c.f. conftest.py)
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_dao

import pandas as pd

from business_object.pays import Pays
from dao.pays_dao import PaysDAO


def df_pays_test():
    """Un pays de test qui n'existe pas en vrai"""
    return pd.DataFrame({"code_iso": ["ZZZ"], "nom_pays": ["Testland"]})


def test_enregistrer_puis_lister():
    # GIVEN
    dao = PaysDAO()
    # WHEN
    nb = dao.enregistrer(df_pays_test())
    # THEN
    assert nb == 1
    assert Pays("ZZZ", "Testland") in dao.lister()


def test_enregistrer_deux_fois_ne_cree_pas_de_doublon():
    # GIVEN
    dao = PaysDAO()
    dao.enregistrer(df_pays_test())
    # WHEN : même pays une deuxième fois (ON CONFLICT DO NOTHING)
    dao.enregistrer(df_pays_test())
    # THEN
    codes = [pays.code_iso for pays in dao.lister()]
    assert codes.count("ZZZ") == 1


def test_enregistrer_dataframe_vide():
    # WHEN
    nb = PaysDAO().enregistrer(pd.DataFrame(columns=["code_iso", "nom_pays"]))
    # THEN
    assert nb == 0
