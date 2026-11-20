"""Tests d'intégration API pour le contrôleur Multi-Indicateurs (F5)."""

from unittest.mock import patch

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controller import multi_indicateurs_controller

# On n'importe pas main.py : il interroge la base dès l'import (UtilisateurService().initialiser_admin()).
# Petite application avec seulement le routeur testé, au même préfixe que dans main.py.
app = FastAPI()
app.include_router(multi_indicateurs_controller.router, prefix="/analyses")
client = TestClient(app)


@pytest.fixture
def payload_valide() -> dict:
    """Corps de requête valide, au format envoyé par la page Streamlit : 2 sélections + base 100."""
    return {
        "selections": [
            {"indicateur": "EMP_5EMP_SEX_OC2_NB_Q", "pays": "FRA", "classif1": "Total", "sexe": "Total"},
            {"indicateur": "EMP_5WAP_SEX_AGE_RT_Q", "pays": "FRA", "classif1": "15+", "sexe": "Total"},
        ],
        "base_100": True,
    }


SELECTION = {"indicateur": "EMP_5WAP_SEX_AGE_RT_Q", "pays": "FRA", "classif1": "15+", "sexe": "Total"}


@pytest.mark.parametrize("nb_selections", [0, 5])
def test_route_nombre_de_selections_invalide_renvoie_422(nb_selections):
    """Le schéma impose 1 à 4 sélections : FastAPI rejette la requête lui-même (422)."""
    payload = {"selections": [SELECTION] * nb_selections, "base_100": True}
    with patch("service.multi_indicateurs_service.MultiIndicateursService.comparer") as faux_comparer:
        response = client.post("/analyses/multi-indicateurs", json=payload)

    assert response.status_code == 422
    faux_comparer.assert_not_called()  # le service n'est jamais appelé


def test_route_succes_retourne_200_et_donnees(payload_valide):
    """Vérifie le statut 200 et la structure JSON de la réponse."""
    df_simule = pd.DataFrame(
        [
            {
                "serie": "Emploi — FRA — Total — Total",
                "indicateur": "EMP_5EMP_SEX_OC2_NB_Q",
                "periode": "2024Q1",
                "valeur": 1000.0,
                "unite": "milliers",
                "valeur_base100": 100.0,
            },
            {
                "serie": "Taux — FRA — Total — 15+",
                "indicateur": "EMP_5WAP_SEX_AGE_RT_Q",
                "periode": "2024Q1",
                "valeur": 68.5,
                "unite": "%",
                "valeur_base100": 100.0,
            },
        ]
    )

    with patch(
        "service.multi_indicateurs_service.MultiIndicateursService.comparer", return_value=df_simule
    ):
        response = client.post("/analyses/multi-indicateurs", json=payload_valide)

    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == 2
    assert json_data[0]["valeur_base100"] == 100.0


def test_route_erreur_frequences_renvoie_400(payload_valide):
    """Vérifie la capture d'une erreur métier et le retour 400."""
    with patch(
        "service.multi_indicateurs_service.MultiIndicateursService.comparer",
        side_effect=ValueError("Les indicateurs ont des fréquences différentes."),
    ):
        response = client.post("/analyses/multi-indicateurs", json=payload_valide)

    assert response.status_code == 400
    assert "fréquences différentes" in response.json()["detail"]
