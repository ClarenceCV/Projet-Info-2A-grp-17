# Tests de JournalDAO sur la vraie base (pseudos 'test_dao...', supprimés après chaque test : c.f. conftest.py)
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_dao

from business_object.action_journal import ActionJournal
from dao.journal_dao import JournalDAO


def test_enregistrer_puis_lister():
    # GIVEN
    dao = JournalDAO()
    # WHEN
    ok = dao.enregistrer(ActionJournal(action="connexion", pseudo="test_dao_jean", detail="test"))
    actions = dao.lister(pseudo="test_dao_jean")
    # THEN
    assert ok
    assert len(actions) == 1
    assert actions[0].action == "connexion"
    assert actions[0].date is not None  # remplie par la base


def test_lister_filtre_par_action():
    # GIVEN
    dao = JournalDAO()
    dao.enregistrer(ActionJournal(action="connexion", pseudo="test_dao_jean"))
    dao.enregistrer(ActionJournal(action="deconnexion", pseudo="test_dao_jean"))
    # WHEN
    actions = dao.lister(action="deconnexion", pseudo="test_dao")
    # THEN
    assert [a.action for a in actions] == ["deconnexion"]


def test_lister_les_plus_recentes_d_abord():
    # GIVEN
    dao = JournalDAO()
    dao.enregistrer(ActionJournal(action="connexion", pseudo="test_dao_jean"))
    dao.enregistrer(ActionJournal(action="deconnexion", pseudo="test_dao_jean"))
    # WHEN
    actions = dao.lister(pseudo="test_dao")
    # THEN
    assert [a.action for a in actions] == ["deconnexion", "connexion"]


def test_lister_respecte_la_limite():
    # GIVEN
    dao = JournalDAO()
    for _ in range(3):
        dao.enregistrer(ActionJournal(action="connexion", pseudo="test_dao_jean"))
    # WHEN
    actions = dao.lister(pseudo="test_dao", limite=2)
    # THEN
    assert len(actions) == 2
