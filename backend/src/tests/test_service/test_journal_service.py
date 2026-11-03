# Tests du service du journal des actions (F6). Le DAO est remplacé par un faux (patch.object).
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests

from unittest.mock import patch

from business_object.utilisateur import Utilisateur
from dao.journal_dao import JournalDAO
from service.journal_service import JournalService

JDUPONT = Utilisateur(pseudo="jdupont", role="utilisateur", id=1)


def test_enregistrer_une_action():
    # GIVEN
    with patch.object(JournalDAO, "enregistrer", return_value=True) as faux_enregistrer:
        # WHEN
        ok = JournalService().enregistrer(JDUPONT, "connexion")
    # THEN : l'action envoyée au DAO contient l'id et le pseudo de l'utilisateur
    entree = faux_enregistrer.call_args.args[0]
    assert ok
    assert (entree.utilisateur_id, entree.pseudo, entree.action) == (1, "jdupont", "connexion")


def test_enregistrer_sans_utilisateur_garde_le_pseudo_essaye():
    with patch.object(JournalDAO, "enregistrer", return_value=True) as faux_enregistrer:
        JournalService().enregistrer(None, "echec_connexion", pseudo="pirate")
    entree = faux_enregistrer.call_args.args[0]
    assert (entree.utilisateur_id, entree.pseudo) == (None, "pirate")


def test_une_panne_du_journal_ne_bloque_pas():
    # GIVEN : la base refuse l'écriture
    with patch.object(JournalDAO, "enregistrer", side_effect=RuntimeError("base indisponible")):
        # WHEN / THEN : pas d'exception, simplement False
        assert JournalService().enregistrer(JDUPONT, "connexion") is False


def test_action_inconnue_refusee():
    with patch.object(JournalDAO, "enregistrer") as faux_enregistrer:
        assert JournalService().enregistrer(JDUPONT, "action_inventee") is False
    faux_enregistrer.assert_not_called()
