# Tests des endpoints des comptes (F6) : /login, /logout, /utilisateurs, /admin/utilisateurs, /admin/journal.
#
# On utilise TestClient (fourni par FastAPI) : il envoie de vraies requêtes HTTP à l'application,
# sans lancer de serveur. Les services sont remplacés par des faux : pas de base de données.
#
# On n'importe PAS main.py : il se connecte à la base dès l'import. On construit à la place une petite
# application avec les mêmes routeurs et les mêmes préfixes que dans main.py.
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_controller/test_comptes_controller.py

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from business_object.action_journal import ActionJournal
from business_object.utilisateur import Utilisateur
from controller import admin_utilisateur_controller, journal_controller, login_controller, utilisateur_controller
from service.journal_service import JournalService
from service.utilisateur_service import UtilisateurService

JDUPONT = Utilisateur(pseudo="jdupont", role="utilisateur", id=1)
ADMIN = Utilisateur(pseudo="admin", role="admin", id=2)

# Faux tokens : l'en-tête X-Auth-Token à envoyer pour être « connecté » en tant que...
EN_TETE_USER = {"X-Auth-Token": "token-user"}
EN_TETE_ADMIN = {"X-Auth-Token": "token-admin"}
TOKENS = {"token-user": JDUPONT, "token-admin": ADMIN}

app = FastAPI()
app.include_router(login_controller.router)
app.include_router(utilisateur_controller.router, prefix="/utilisateurs")
app.include_router(admin_utilisateur_controller.router, prefix="/admin/utilisateurs")
app.include_router(journal_controller.router, prefix="/admin/journal")
client = TestClient(app)


@pytest.fixture(autouse=True)
def faux_tokens_et_journal():
    """
    Avant CHAQUE test (autouse=True) :
    - trouver_par_token est remplacé par une recherche dans le dictionnaire TOKENS
      (side_effect : le faux appelle TOKENS.get(token), donc un token inconnu donne None → 401) ;
    - le journal est remplacé par un faux, pour ne rien écrire.
    """
    with patch.object(UtilisateurService, "trouver_par_token", side_effect=TOKENS.get), \
         patch.object(JournalService, "enregistrer", return_value=True):
        yield


# --- POST /login, POST /logout ----------------------------------------------------------


def test_login_ok_renvoie_token_et_utilisateur():
    # GIVEN
    with patch.object(UtilisateurService, "se_connecter", return_value=(JDUPONT, "nouveau-token")):
        # WHEN
        reponse = client.post("/login", json={"pseudo": "jdupont", "mot_de_passe": "motdepasse123"})
    # THEN
    assert reponse.status_code == 200
    assert reponse.json()["token"] == "nouveau-token"
    assert reponse.json()["utilisateur"]["pseudo"] == "jdupont"


def test_login_identifiants_invalides_401():
    with patch.object(UtilisateurService, "se_connecter", return_value=None):
        reponse = client.post("/login", json={"pseudo": "jdupont", "mot_de_passe": "mauvais"})
    assert reponse.status_code == 401


def test_login_corps_incomplet_422():
    # pas de mot_de_passe : refusé par Pydantic (IdentifiantsModel) avant même d'appeler le service
    reponse = client.post("/login", json={"pseudo": "jdupont"})
    assert reponse.status_code == 422


def test_logout_connecte():
    with patch.object(UtilisateurService, "se_deconnecter", return_value=True) as faux:
        reponse = client.post("/logout", headers=EN_TETE_USER)
    assert reponse.status_code == 200
    faux.assert_called_once_with(JDUPONT)


def test_logout_sans_token_401():
    assert client.post("/logout").status_code == 401


# --- /utilisateurs ------------------------------------------------------------------------


def test_moi_renvoie_l_utilisateur_du_token():
    reponse = client.get("/utilisateurs/moi", headers=EN_TETE_USER)
    assert reponse.status_code == 200
    assert reponse.json()["pseudo"] == "jdupont"


@pytest.mark.parametrize("en_tetes", [{}, {"X-Auth-Token": "token-inconnu"}])
def test_moi_sans_token_valide_401(en_tetes):
    assert client.get("/utilisateurs/moi", headers=en_tetes).status_code == 401


def test_creer_compte_201():
    with patch.object(UtilisateurService, "creer_compte", return_value=JDUPONT) as faux:
        reponse = client.post("/utilisateurs", json={"pseudo": "jdupont", "mot_de_passe": "motdepasse123"})
    assert reponse.status_code == 201
    faux.assert_called_once_with("jdupont", "motdepasse123")  # aucun rôle transmis : 'utilisateur'


def test_creer_compte_pas_de_mot_de_passe_dans_la_reponse():
    with patch.object(UtilisateurService, "creer_compte", return_value=JDUPONT):
        reponse = client.post("/utilisateurs", json={"pseudo": "jdupont", "mot_de_passe": "motdepasse123"})
    assert set(reponse.json()) == {"id", "pseudo", "role", "date_creation"}


def test_creer_compte_pseudo_deja_pris_400():
    with patch.object(UtilisateurService, "creer_compte", return_value=None):
        reponse = client.post("/utilisateurs", json={"pseudo": "jdupont", "mot_de_passe": "motdepasse123"})
    assert reponse.status_code == 400


def test_creer_compte_valeur_invalide_400_avec_message():
    with patch.object(UtilisateurService, "creer_compte", side_effect=ValueError("Mot de passe trop court.")):
        reponse = client.post("/utilisateurs", json={"pseudo": "jdupont", "mot_de_passe": "court"})
    assert reponse.status_code == 400
    assert reponse.json()["detail"] == "Mot de passe trop court."


def test_creer_compte_ne_permet_pas_de_devenir_admin():
    # un champ 'role' envoyé à POST /utilisateurs est ignoré : le service ne le reçoit pas
    with patch.object(UtilisateurService, "creer_compte", return_value=JDUPONT) as faux:
        client.post("/utilisateurs", json={"pseudo": "pirate", "mot_de_passe": "motdepasse123", "role": "admin"})
    faux.assert_called_once_with("pirate", "motdepasse123")


# --- /admin/utilisateurs : droits ---------------------------------------------------------


@pytest.mark.parametrize(
    "methode, chemin",
    [("GET", "/admin/utilisateurs"), ("POST", "/admin/utilisateurs"), ("DELETE", "/admin/utilisateurs/1"),
     ("GET", "/admin/journal")],
)
def test_admin_refuse_sans_token_401_et_utilisateur_simple_403(methode, chemin):
    corps = {"pseudo": "marie", "mot_de_passe": "motdepasse123"} if methode == "POST" else None
    assert client.request(methode, chemin, json=corps).status_code == 401
    assert client.request(methode, chemin, json=corps, headers=EN_TETE_USER).status_code == 403


# --- /admin/utilisateurs : actions --------------------------------------------------------


def test_admin_lister():
    with patch.object(UtilisateurService, "lister", return_value=[ADMIN, JDUPONT]):
        reponse = client.get("/admin/utilisateurs", headers=EN_TETE_ADMIN)
    assert reponse.status_code == 200
    assert [u["pseudo"] for u in reponse.json()] == ["admin", "jdupont"]


def test_admin_creer_un_admin():
    marie = Utilisateur(pseudo="marie", role="admin", id=3)
    with patch.object(UtilisateurService, "creer_compte", return_value=marie) as faux:
        reponse = client.post(
            "/admin/utilisateurs", headers=EN_TETE_ADMIN,
            json={"pseudo": "marie", "mot_de_passe": "motdepasse123", "role": "admin"},
        )
    assert reponse.status_code == 201
    assert reponse.json()["role"] == "admin"
    # le rôle choisi est transmis, et l'admin est noté comme auteur (pour le journal)
    faux.assert_called_once_with("marie", "motdepasse123", "admin", auteur=ADMIN)


def test_admin_creer_role_inconnu_422():
    # Literal["utilisateur", "admin"] dans CreationUtilisateurModel
    reponse = client.post(
        "/admin/utilisateurs", headers=EN_TETE_ADMIN,
        json={"pseudo": "marie", "mot_de_passe": "motdepasse123", "role": "superadmin"},
    )
    assert reponse.status_code == 422


def test_admin_supprimer_ok():
    with patch.object(UtilisateurService, "supprimer", return_value=True) as faux:
        reponse = client.delete("/admin/utilisateurs/1", headers=EN_TETE_ADMIN)
    assert reponse.status_code == 200
    faux.assert_called_once_with(ADMIN, 1)


def test_admin_supprimer_inexistant_404():
    with patch.object(UtilisateurService, "supprimer", return_value=False):
        assert client.delete("/admin/utilisateurs/999", headers=EN_TETE_ADMIN).status_code == 404


def test_admin_supprimer_son_propre_compte_400():
    with patch.object(UtilisateurService, "supprimer", side_effect=ValueError("propre compte")):
        assert client.delete("/admin/utilisateurs/2", headers=EN_TETE_ADMIN).status_code == 400


# --- /admin/journal -----------------------------------------------------------------------


def test_journal_renvoie_les_actions_avec_leur_libelle():
    action = ActionJournal(action="echec_connexion", pseudo="pirate", id=7, date=datetime(2026, 11, 5, 10, 0))
    with patch.object(JournalService, "lister", return_value=[action]) as faux:
        reponse = client.get(
            "/admin/journal", headers=EN_TETE_ADMIN, params={"action": "echec_connexion", "limite": 10}
        )
    assert reponse.status_code == 200
    assert reponse.json()[0]["libelle_action"] == "Échec de connexion"
    faux.assert_called_once_with("echec_connexion", None, 10)  # les filtres sont transmis au service


def test_journal_limite_hors_bornes_422():
    assert client.get("/admin/journal", headers=EN_TETE_ADMIN, params={"limite": 0}).status_code == 422
