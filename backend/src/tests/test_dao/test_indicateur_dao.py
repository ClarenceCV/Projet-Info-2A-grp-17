# Tests d'IndicateurDAO sur la vraie base (indicateur de test 'TEST_DAO', supprimé après chaque test : c.f. conftest.py)
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_dao

from business_object.indicateur import Indicateur
from dao.indicateur_dao import IndicateurDAO

INDICATEUR_TEST = Indicateur(
    code="TEST_DAO", libelle="Indicateur de test", unite="%", frequence="Q", nom_classif1="tranche_age"
)


def test_enregistrer_renvoie_un_id():
    # WHEN
    id_indicateur = IndicateurDAO().enregistrer(INDICATEUR_TEST)
    # THEN
    assert isinstance(id_indicateur, int)


def test_enregistrer_puis_trouver_par_code():
    # GIVEN
    dao = IndicateurDAO()
    dao.enregistrer(INDICATEUR_TEST)
    # WHEN
    indicateur = dao.trouver_par_code("TEST_DAO")
    # THEN
    assert indicateur == INDICATEUR_TEST


def test_enregistrer_deux_fois_met_a_jour():
    # GIVEN
    dao = IndicateurDAO()
    premier_id = dao.enregistrer(INDICATEUR_TEST)
    nouveau = Indicateur(code="TEST_DAO", libelle="Nouveau libellé", unite="%", frequence="Q")
    # WHEN : même code (ON CONFLICT DO UPDATE)
    deuxieme_id = dao.enregistrer(nouveau)
    # THEN : même ligne, libellé mis à jour
    assert deuxieme_id == premier_id
    assert dao.trouver_par_code("TEST_DAO").libelle == "Nouveau libellé"


def test_trouver_par_code_inconnu():
    # WHEN
    indicateur = IndicateurDAO().trouver_par_code("CODE_QUI_N_EXISTE_PAS")
    # THEN
    assert indicateur is None


def test_lister_contient_l_indicateur():
    # GIVEN
    dao = IndicateurDAO()
    dao.enregistrer(INDICATEUR_TEST)
    # WHEN
    indicateurs = dao.lister()
    # THEN
    assert INDICATEUR_TEST in indicateurs
