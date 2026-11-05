# Tests des gardes de controller/auth.py, en appelant les fonctions directement (sans FastAPI).
# Le service est remplacé par un faux (patch.object) : pas de base de données.
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_controller/test_auth.py

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from business_object.utilisateur import Utilisateur
from controller.auth import admin_requis, utilisateur_connecte
from service.utilisateur_service import UtilisateurService

JDUPONT = Utilisateur(pseudo="jdupont", role="utilisateur", id=1)
ADMIN = Utilisateur(pseudo="admin", role="admin", id=2)


# --- utilisateur_connecte -----------------------------------------------------------------


def test_utilisateur_connecte_token_valide():
    # GIVEN : le service reconnaît le token
    with patch.object(UtilisateurService, "trouver_par_token", return_value=JDUPONT) as faux:
        # WHEN
        utilisateur = utilisateur_connecte("bon-token")
    # THEN : on récupère l'utilisateur, et le service a reçu le token tel quel
    assert utilisateur == JDUPONT
    faux.assert_called_once_with("bon-token")


@pytest.mark.parametrize("token", [None, "token-inconnu"])
def test_utilisateur_connecte_sans_token_valide_401(token):
    # GIVEN : en-tête absent (None) ou token inconnu / effacé par une déconnexion
    with patch.object(UtilisateurService, "trouver_par_token", return_value=None):
        # WHEN / THEN
        with pytest.raises(HTTPException) as erreur:
            utilisateur_connecte(token)
    assert erreur.value.status_code == 401


# --- admin_requis -------------------------------------------------------------------------


def test_admin_requis_utilisateur_simple_403():
    # admin_requis reçoit l'utilisateur déjà trouvé par utilisateur_connecte
    with pytest.raises(HTTPException) as erreur:
        admin_requis(JDUPONT)
    assert erreur.value.status_code == 403


def test_admin_requis_admin_ok():
    assert admin_requis(ADMIN) == ADMIN
