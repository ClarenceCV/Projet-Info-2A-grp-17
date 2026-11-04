# Tests d'ObservationDAO sur la vraie base
# (pays 'ZZZ' et indicateur 'TEST_DAO', supprimés après chaque test avec leurs observations : c.f. conftest.py)
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_dao

import pandas as pd

from business_object.indicateur import Indicateur
from dao.indicateur_dao import IndicateurDAO
from dao.observation_dao import ObservationDAO
from dao.pays_dao import PaysDAO
from schema.observation_model import CleObservationModel


def preparer_base() -> int:
    """
    Enregistre le pays et l'indicateur de test (une observation en a besoin).

    Returns:
        int: id de l'indicateur de test
    """
    PaysDAO().enregistrer(pd.DataFrame({"code_iso": ["ZZZ"], "nom_pays": ["Testland"]}))
    return IndicateurDAO().enregistrer(
        Indicateur(code="TEST_DAO", libelle="Indicateur de test", unite="%", frequence="Q")
    )


def df_observations():
    """2 observations de test : Total et Female, au 2024Q4"""
    return pd.DataFrame({
        "code_iso": ["ZZZ", "ZZZ"],
        "source": ["TEST", "TEST"],
        "periode": ["2024Q4", "2024Q4"],
        "sexe": ["Total", "Female"],
        "classif1": ["15+", "15-24"],
        "valeur": [50.0, 40.0],
        "statut": [None, None],
    })


def cle_total(indicateur_id: int) -> CleObservationModel:
    """Clé de l'observation de test 'Total'"""
    return CleObservationModel(
        indicateur_id=indicateur_id, code_iso="ZZZ", source="TEST",
        periode="2024Q4", sexe="Total", classif1="15+",
    )


def test_enregistrer_puis_lire():
    # GIVEN
    indicateur_id = preparer_base()
    dao = ObservationDAO()
    # WHEN
    nb = dao.enregistrer(indicateur_id, df_observations())
    df = dao.lire("TEST_DAO")
    # THEN : 2 lignes, avec le nom du pays et l'unité de l'indicateur
    assert nb == 2
    assert len(df) == 2
    assert list(df["nom_pays"].unique()) == ["Testland"]
    assert list(df["unite"].unique()) == ["%"]


def test_enregistrer_deux_fois_met_a_jour_la_valeur():
    # GIVEN
    indicateur_id = preparer_base()
    dao = ObservationDAO()
    dao.enregistrer(indicateur_id, df_observations())
    nouveau = df_observations()
    nouveau["valeur"] = [99.0, 40.0]
    # WHEN : mêmes clés (ON CONFLICT DO UPDATE)
    dao.enregistrer(indicateur_id, nouveau)
    df = dao.lire("TEST_DAO", sexe="Total")
    # THEN : pas de doublon, valeur mise à jour
    assert len(df) == 1
    assert df["valeur"].iloc[0] == 99.0


def test_enregistrer_dataframe_vide():
    # WHEN
    nb = ObservationDAO().enregistrer(1, pd.DataFrame())
    # THEN
    assert nb == 0


def test_lire_avec_filtres():
    # GIVEN
    indicateur_id = preparer_base()
    dao = ObservationDAO()
    dao.enregistrer(indicateur_id, df_observations())
    # WHEN
    df = dao.lire("TEST_DAO", pays=["ZZZ"], sexe="Female", classif1="15-24")
    # THEN
    assert len(df) == 1
    assert df["valeur"].iloc[0] == 40.0


def test_lire_indicateur_inconnu_renvoie_dataframe_vide():
    # WHEN
    df = ObservationDAO().lire("CODE_QUI_N_EXISTE_PAS")
    # THEN : vide, mais avec les bonnes colonnes
    assert df.empty
    assert "valeur" in df.columns


def test_lister_classif1():
    # GIVEN
    indicateur_id = preparer_base()
    ObservationDAO().enregistrer(indicateur_id, df_observations())
    # WHEN
    modalites = ObservationDAO().lister_classif1("TEST_DAO")
    # THEN : sans doublon et triées
    assert modalites == ["15+", "15-24"]


def test_modifier():
    # GIVEN
    indicateur_id = preparer_base()
    dao = ObservationDAO()
    dao.enregistrer(indicateur_id, df_observations())
    # WHEN
    ok = dao.modifier(cle_total(indicateur_id), 77.0)
    # THEN
    assert ok
    assert dao.lire("TEST_DAO", sexe="Total")["valeur"].iloc[0] == 77.0


def test_modifier_observation_inexistante():
    # GIVEN : la base ne contient pas l'observation
    indicateur_id = preparer_base()
    # WHEN
    ok = ObservationDAO().modifier(cle_total(indicateur_id), 77.0)
    # THEN
    assert not ok


def test_supprimer():
    # GIVEN
    indicateur_id = preparer_base()
    dao = ObservationDAO()
    dao.enregistrer(indicateur_id, df_observations())
    # WHEN
    ok = dao.supprimer(cle_total(indicateur_id))
    # THEN : il ne reste que l'observation 'Female'
    assert ok
    assert list(dao.lire("TEST_DAO")["sexe"]) == ["Female"]


def test_supprimer_observation_inexistante():
    # GIVEN
    indicateur_id = preparer_base()
    # WHEN
    ok = ObservationDAO().supprimer(cle_total(indicateur_id))
    # THEN
    assert not ok
