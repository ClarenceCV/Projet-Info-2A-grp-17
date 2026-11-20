"""
Tests du service du journal des actions (F6).
Le DAO est remplacé par un faux (patch.object) : les tests ne dépendent pas de la base
et on peut vérifier précisément ce qui lui est transmis.

Lancement (depuis le dossier backend) :
     uv run pytest src/tests
"""

from unittest.mock import patch

from business_object.utilisateur import Utilisateur
from dao.journal_dao import JournalDAO
from service.journal_service import JournalService

JDUPONT = Utilisateur(pseudo="jdupont", role="utilisateur", id=1)


def test_enregistrer_une_action():
    """
    Vérifie qu'une action est transmise au DAO sous forme d'entrée de journal
    contenant l'id et le pseudo de l'utilisateur ainsi que le nom de l'action
    (ici 1, "jdupont", "connexion"), et que le service renvoie True.
    """
    # GIVEN
    with patch.object(JournalDAO, "enregistrer", return_value=True) as faux_enregistrer:
        # WHEN
        ok = JournalService().enregistrer(JDUPONT, "connexion")
    # THEN : l'action envoyée au DAO contient l'id et le pseudo de l'utilisateur
    entree = faux_enregistrer.call_args.args[0]
    assert ok
    assert (entree.utilisateur_id, entree.pseudo, entree.action) == (1, "jdupont", "connexion")


def test_enregistrer_sans_utilisateur_garde_le_pseudo_essaye():
    """
    Vérifie que, sans utilisateur connecté (cas d'un échec de connexion),
    l'entrée de journal n'a pas d'id (None) mais conserve le pseudo essayé
    ("pirate"), ce qui permet de tracer les tentatives suspectes.
    """
    with patch.object(JournalDAO, "enregistrer", return_value=True) as faux_enregistrer:
        JournalService().enregistrer(None, "echec_connexion", pseudo="pirate")
    entree = faux_enregistrer.call_args.args[0]
    assert (entree.utilisateur_id, entree.pseudo) == (None, "pirate")


def test_une_panne_du_journal_ne_bloque_pas():
    """
    Vérifie qu'une erreur du DAO (base indisponible) ne remonte pas jusqu'à
    l'appelant : le service ne lève pas d'exception et renvoie simplement
    False, pour qu'une panne du journal ne bloque pas l'application.
    """
    # GIVEN : la base refuse l'écriture
    with patch.object(JournalDAO, "enregistrer", side_effect=RuntimeError("base indisponible")):
        # WHEN / THEN : pas d'exception, simplement False
        assert JournalService().enregistrer(JDUPONT, "connexion") is False


def test_action_inconnue_refusee():
    """
    Vérifie qu'une action qui ne fait pas partie des actions autorisées est
    refusée : le service renvoie False et le DAO n'est jamais appelé.
    """
    with patch.object(JournalDAO, "enregistrer") as faux_enregistrer:
        assert JournalService().enregistrer(JDUPONT, "action_inventee") is False
    faux_enregistrer.assert_not_called()
