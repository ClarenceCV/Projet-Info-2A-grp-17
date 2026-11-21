"""
Tests du contrôle d'accès des routes de données (indicateurs, pays, observations, analyses,
rapport) : elles sont réservées aux utilisateurs connectés, comme les pages correspondantes du
frontend (un visiteur ne voit que l'accueil, la connexion et la création de compte).

Le contrôle est posé une seule fois par controller, sur le router :
    router = APIRouter(dependencies=[Depends(utilisateur_connecte)])
Ces tests vérifient donc que chaque controller de données a bien ce garde.
Ni base ni service réel : la recherche du token est remplacée par TOKENS.get (c.f. faux_comptes).
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controller import (
    comparaison_pays_controller,
    evolution_controller,
    indicateur_controller,
    multi_indicateurs_controller,
    observation_controller,
    pays_controller,
    rapport_controller,
)
from service.pays_service import PaysService
from service.utilisateur_service import UtilisateurService
from tests.test_controller.faux_comptes import EN_TETE_USER, TOKENS

# Petite application avec les routers testés, aux mêmes préfixes que dans main.py
app = FastAPI()
app.include_router(indicateur_controller.router, prefix="/indicateurs")
app.include_router(observation_controller.router, prefix="/observations")
app.include_router(pays_controller.router, prefix="/pays")
app.include_router(evolution_controller.router, prefix="/analyses")
app.include_router(multi_indicateurs_controller.router, prefix="/analyses")
app.include_router(comparaison_pays_controller.router, prefix="/analyses")
app.include_router(rapport_controller.router)
client = TestClient(app)

# Une route par controller de données (méthode, chemin)
ROUTES_DONNEES = [
    ("get", "/indicateurs"),
    ("get", "/indicateurs/EMP_5WAP_SEX_AGE_RT_Q"),
    ("get", "/indicateurs/EMP_5WAP_SEX_AGE_RT_Q/classif1"),
    ("get", "/pays"),
    ("get", "/observations"),
    ("get", "/analyses/evolution"),
    ("get", "/analyses/comparaison-pays"),
    ("post", "/analyses/multi-indicateurs"),
    ("get", "/rapport"),
]


@pytest.fixture(autouse=True, name="faux_tokens")
def fixture_faux_tokens():
    """Avant chaque test : seuls les faux tokens de TOKENS sont reconnus."""
    with patch.object(UtilisateurService, "trouver_par_token", side_effect=TOKENS.get):
        yield


@pytest.mark.parametrize("methode, chemin", ROUTES_DONNEES)
def test_route_de_donnees_sans_token_renvoie_401(methode, chemin):
    # WHEN : un visiteur (aucun en-tête X-Auth-Token) appelle la route
    reponse = client.request(methode, chemin)
    # THEN : refusé avant même de lire les paramètres ou d'appeler un service
    assert reponse.status_code == 401
    assert reponse.json()["detail"] == "Connexion requise."


@pytest.mark.parametrize("methode, chemin", ROUTES_DONNEES)
def test_route_de_donnees_token_inconnu_renvoie_401(methode, chemin):
    # token inventé, ou effacé par une déconnexion
    reponse = client.request(methode, chemin, headers={"X-Auth-Token": "token-invente"})
    assert reponse.status_code == 401


def test_route_de_donnees_avec_token_valide_repond():
    # GIVEN : un utilisateur connecté, et un faux service qui renvoie un pays
    with patch.object(
        PaysService, "lister", return_value=[{"code_iso": "FRA", "nom_pays": "France"}]
    ):
        # WHEN
        reponse = client.get("/pays", headers=EN_TETE_USER)
    # THEN : le garde laisse passer, la route répond normalement
    assert reponse.status_code == 200
    assert reponse.json() == [{"code_iso": "FRA", "nom_pays": "France"}]
