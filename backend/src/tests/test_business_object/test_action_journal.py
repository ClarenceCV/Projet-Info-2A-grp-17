# Tests de l'objet métier ActionJournal (une ligne du journal des actions).
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_business_object

import pytest

from business_object.action_journal import ACTIONS, ActionJournal


def test_creation_minimale():
    # WHEN : seule l'action est obligatoire
    entree = ActionJournal(action="connexion")
    # THEN : le reste vaut None (id et date sont remplis par la base)
    assert (entree.pseudo, entree.detail, entree.utilisateur_id, entree.id, entree.date) == (
        None, None, None, None, None,
    )


@pytest.mark.parametrize("action", list(ACTIONS))
def test_toutes_les_actions_connues_sont_acceptees(action):
    assert ActionJournal(action=action).action == action


@pytest.mark.parametrize("action", ["action_inventee", "", "Connexion"])
def test_action_inconnue_refusee(action):
    # 'Connexion' est un libellé, pas une clé : refusé aussi
    with pytest.raises(ValueError):
        ActionJournal(action=action)


def test_chaque_action_a_un_libelle():
    # les libellés sont affichés dans la page historique : aucun ne doit être vide
    assert all(isinstance(libelle, str) and libelle for libelle in ACTIONS.values())
