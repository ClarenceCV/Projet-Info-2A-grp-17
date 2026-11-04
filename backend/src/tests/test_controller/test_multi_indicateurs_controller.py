"""Tests d'intégration API pour le contrôleur Multi-Indicateurs (F5)."""

from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.fixture
def payload_valide() -> list[dict[str, str]]:
    """Payload HTTP avec 2 sélections valides."""
    return [
        {"indicateur": "EMP_5EMP_SEX_OC2_NB_Q", "pays": "FRA", "classif1": "Total", "sexe": "Total"},
        {"indicateur": "EMP_5WAP_SEX_AGE_RT_Q", "pays": "FRA", "classif1": "15+", "sexe": "Total"},
    ]


def test_route_moins_de_deux_selections_renvoie_400():
    """Vérifie le rejet HTTP 400 si moins de 2 sélections sont fournies."""
    payload = [{"indicateur": "EMP_5EMP_SEX_OC2_NB_Q", "pays": "FRA", "classif1": "Total", "sexe": "Total"}]
    response = client.post("/analyses/multi-indicateurs", json=payload)

    assert response.status_code == 400
    assert "Au moins 2 sélections" in response.json()["detail"]


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

    with patch("service.multi_indicateurs_service.MultiIndicateursService.comparer", return_value=df_simule):
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
