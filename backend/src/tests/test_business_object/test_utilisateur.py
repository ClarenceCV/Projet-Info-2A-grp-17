# Tests de l'objet métier Utilisateur (vérifications faites à la création, propriété est_admin).
# Pas de base, pas de faux objet : on teste seulement la classe.
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_business_object

import pytest

from business_object.utilisateur import Utilisateur


def test_creation_valeurs_par_defaut():
    # WHEN
    utilisateur = Utilisateur(pseudo="jdupont")
    # THEN : rôle 'utilisateur', pas encore d'id ni de date (remplis par la base)
    assert utilisateur.role == "utilisateur"
    assert utilisateur.id is None
    assert utilisateur.date_creation is None


@pytest.mark.parametrize("pseudo", ["", None, 42])
def test_pseudo_invalide(pseudo):
    with pytest.raises(ValueError):
        Utilisateur(pseudo=pseudo)


def test_role_invalide():
    # seuls 'utilisateur' et 'admin' sont acceptés (même liste que la contrainte CHECK en base)
    with pytest.raises(ValueError):
        Utilisateur(pseudo="jdupont", role="superadmin")


@pytest.mark.parametrize("role, attendu", [("admin", True), ("utilisateur", False)])
def test_est_admin(role, attendu):
    assert Utilisateur(pseudo="jdupont", role=role).est_admin is attendu


def test_str():
    assert str(Utilisateur(pseudo="jdupont", role="admin")) == "jdupont (admin)"


def test_pas_d_attribut_mot_de_passe():
    # le hash ne doit jamais faire partie de l'objet (il ne peut donc pas sortir par l'API)
    utilisateur = Utilisateur(pseudo="jdupont")
    assert not hasattr(utilisateur, "mot_de_passe")
    assert not hasattr(utilisateur, "mdp_hash")


def test_egalite():
    # @dataclass génère __eq__ : deux objets aux mêmes attributs sont égaux
    assert Utilisateur("jdupont", id=1) == Utilisateur("jdupont", id=1)
    assert Utilisateur("jdupont", id=1) != Utilisateur("jdupont", id=2)
