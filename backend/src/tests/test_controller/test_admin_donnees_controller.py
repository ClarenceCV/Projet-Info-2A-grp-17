"""
Tests des endpoints d'administration des données (/admin/import, /admin/observations, /admin/logs).
Les services (import, observations, journal) sont remplacés par des faux : ni base, ni réseau.
On vérifie surtout : la sécurité (401 / 403), les codes d'erreur, et que le journal n'est
rempli que pour une action qui a vraiment eu lieu.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from business_object.utilisateur import Utilisateur
from controller import admin_donnees_controller
from fetcher.data_processing import DataProcessing
from service.journal_service import JournalService
from service.observation_service import ObservationService
from service.utilisateur_service import UtilisateurService

JDUPONT = Utilisateur(pseudo="jdupont", role="utilisateur", id=1)
ADMIN = Utilisateur(pseudo="admin", role="admin", id=2)
EN_TETE_USER = {"X-Auth-Token": "token-user"}
EN_TETE_ADMIN = {"X-Auth-Token": "token-admin"}
TOKENS = {"token-user": JDUPONT, "token-admin": ADMIN}

# Une observation, identifiée par sa clé (corps des requêtes PUT et DELETE)
CLE = {
    "indicateur": "EMP_5WAP_SEX_AGE_RT_Q", "code_iso": "FRA", "source": "LFS - Employment Survey",
    "periode": "2024Q4", "sexe": "Female", "classif1": "15-24",
}

# Petite application avec seulement le routeur testé, au même préfixe que dans main.py
app = FastAPI()
app.include_router(admin_donnees_controller.router, prefix="/admin")
client = TestClient(app)


@pytest.fixture(autouse=True)
def faux_journal():
    """Avant chaque test : faux tokens (c.f. TOKENS) et faux journal, que le test peut inspecter."""
    with patch.object(UtilisateurService, "trouver_par_token", side_effect=TOKENS.get), \
         patch.object(JournalService, "enregistrer", return_value=True) as faux:
        yield faux


# --- Sécurité ----------------------------------------------------------------------------


@pytest.mark.parametrize("methode, chemin", [
    ("post", "/admin/import"),
    ("put", "/admin/observations?nouvelle_valeur=1"),
    ("delete", "/admin/observations"),
    ("get", "/admin/logs"),
])
def test_routes_reservees_aux_admins(methode, chemin):
    # sans token : 401 (pas connecté) ; avec un compte simple : 403 (connecté mais pas admin)
    corps = {"json": CLE} if methode in ("put", "delete") else {}
    assert client.request(methode, chemin, **corps).status_code == 401
    assert client.request(methode, chemin, headers=EN_TETE_USER, **corps).status_code == 403


# --- Import ------------------------------------------------------------------------------


def test_import_renvoie_le_nombre_d_observations(faux_journal):
    with patch.object(DataProcessing, "charger", return_value=1234):
        reponse = client.post("/admin/import", headers=EN_TETE_ADMIN)
    assert reponse.status_code == 200
    assert reponse.json()["observations_enregistrees"] == 1234
    faux_journal.assert_called_once_with(ADMIN, "import_donnees", "1234 observations enregistrées")


# --- Modification / suppression ------------------------------------------------------------


def test_modifier_observation_ok_et_notee_au_journal(faux_journal):
    with patch.object(ObservationService, "modifier", return_value=True) as faux_modifier:
        reponse = client.put("/admin/observations", params={"nouvelle_valeur": 12.5},
                             json=CLE, headers=EN_TETE_ADMIN)
    assert reponse.status_code == 200
    assert faux_modifier.call_args.args[1] == 12.5
    utilisateur, action, detail = faux_journal.call_args.args
    assert (utilisateur, action) == (ADMIN, "modification_donnee")
    assert "FRA" in detail and "12.5" in detail


def test_modifier_observation_introuvable_404_rien_au_journal(faux_journal):
    with patch.object(ObservationService, "modifier", return_value=False):
        reponse = client.put("/admin/observations", params={"nouvelle_valeur": 12.5},
                             json=CLE, headers=EN_TETE_ADMIN)
    assert reponse.status_code == 404
    faux_journal.assert_not_called()  # rien n'a été modifié : rien à noter


def test_supprimer_observation_ok_et_notee_au_journal(faux_journal):
    with patch.object(ObservationService, "supprimer", return_value=True):
        reponse = client.request("DELETE", "/admin/observations", json=CLE, headers=EN_TETE_ADMIN)
    assert reponse.status_code == 200
    assert faux_journal.call_args.args[:2] == (ADMIN, "suppression_donnee")


def test_supprimer_observation_introuvable_404_rien_au_journal(faux_journal):
    with patch.object(ObservationService, "supprimer", return_value=False):
        reponse = client.request("DELETE", "/admin/observations", json=CLE, headers=EN_TETE_ADMIN)
    assert reponse.status_code == 404
    faux_journal.assert_not_called()


def test_journal_indisponible_ne_bloque_pas_la_suppression(faux_journal):
    # le journal échoue : la suppression a bien eu lieu, l'admin doit recevoir 200 (pas 500)
    faux_journal.return_value = False
    with patch.object(ObservationService, "supprimer", return_value=True):
        reponse = client.request("DELETE", "/admin/observations", json=CLE, headers=EN_TETE_ADMIN)
    assert reponse.status_code == 200


# --- Logs ------------------------------------------------------------------------------------


def test_logs_renvoie_les_dernieres_lignes(tmp_path):
    # GIVEN : un faux fichier de logs de 10 lignes (tmp_path : dossier temporaire fourni par pytest)
    (tmp_path / "laborscope.log").write_text("".join(f"ligne {i}\n" for i in range(10)), encoding="utf-8")
    with patch.object(admin_donnees_controller, "LOG_DIR", tmp_path):
        reponse = client.get("/admin/logs", params={"lignes": 3}, headers=EN_TETE_ADMIN)
    # THEN : seulement les 3 dernières
    assert reponse.status_code == 200
    assert reponse.json()["logs"] == ["ligne 7\n", "ligne 8\n", "ligne 9\n"]


def test_logs_fichier_absent_404(tmp_path):
    with patch.object(admin_donnees_controller, "LOG_DIR", tmp_path):  # dossier vide
        assert client.get("/admin/logs", headers=EN_TETE_ADMIN).status_code == 404
