"""Tests unitaires pour le service MultiIndicateursService (Fonctionnalité F5)."""

from unittest.mock import patch
import pandas as pd
import pytest

from business_object.indicateur import Indicateur
from business_object.selection import Selection
from dao.indicateur_dao import IndicateurDAO
from dao.observation_dao import ObservationDAO
from service.multi_indicateurs_service import MultiIndicateursService


# ------------------------------------------------------------------------------
# Fixtures & Helpers
# ------------------------------------------------------------------------------

@pytest.fixture
def service() -> MultiIndicateursService:
    """Fournit une instance fraîche du service à chaque test."""
    return MultiIndicateursService()


@pytest.fixture
def indicateurs_mock() -> dict[str, Indicateur]:
    """Jeux d'indicateurs factices pour les tests."""
    return {
        "EMP": Indicateur(code="A", libelle="Emploi", unite="milliers", frequence="Q"),
        "TAUX": Indicateur(code="B", libelle="Taux d'emploi", unite="%", frequence="Q"),
        "ANNUEL": Indicateur(code="C", libelle="Taux Annuel", unite="%", frequence="A"),
    }


def creer_dataframe_observation(
    periodes: list[str], valeurs: list[float], unite: str
) -> pd.DataFrame:
    """Génère un DataFrame d'observations simulé."""
    return pd.DataFrame(
        {
            "code_iso": "FRA",
            "nom_pays": "France",
            "source": "LFS",
            "periode": periodes,
            "valeur": valeurs,
            "unite": unite,
        }
    )


# ------------------------------------------------------------------------------
# Cas de tests (Étape 3)
# ------------------------------------------------------------------------------

def test_calcul_base100_et_alignement_periode_commune(
    service: MultiIndicateursService,
    indicateurs_mock: dict[str, Indicateur],
):
    """Vérifie le calcul en base 100 et le rognage avant la première période commune."""
    # GIVEN : Série A (démarre en 2024Q1) et Série B (démarre en 2024Q2)
    obs_a = creer_dataframe_observation(
        periodes=["2024Q1", "2024Q2", "2024Q3"],
        valeurs=[10.0, 20.0, 30.0],
        unite="milliers",
    )
    obs_b = creer_dataframe_observation(
        periodes=["2024Q2", "2024Q3"],
        valeurs=[50.0, 55.0],
        unite="%",
    )

    selections = [
        Selection(indicateur="A", pays="FRA", classif1="Total"),
        Selection(indicateur="B", pays="FRA", classif1="15+"),
    ]

    with patch.object(
        IndicateurDAO,
        "trouver_par_code",
        side_effect=[indicateurs_mock["EMP"], indicateurs_mock["TAUX"]],
    ), patch.object(
        ObservationDAO,
        "lire",
        side_effect=[obs_a, obs_b],
    ):
        # WHEN
        resultat = service.comparer(selections)

    # THEN 1 : Les observations antérieures à 2024Q2 sont exclues
    assert resultat["periode"].min() == "2024Q2"

    # THEN 2 : Chaque série vaut exactement 100.0 à la période commune initiale (2024Q2)
    donnees_communes = resultat[resultat["periode"] == "2024Q2"]
    assert list(donnees_communes["valeur_base100"]) == [100.0, 100.0]

    # THEN 3 : L'évolution relative en 2024Q3 est exacte (Série A : 30.0 / 20.0 * 100 = 150.0)
    serie_a_q3 = resultat[(resultat["indicateur"] == "A") & (resultat["periode"] == "2024Q3")]
    assert serie_a_q3["valeur_base100"].iloc[0] == pytest.approx(150.0)


def test_frequences_differentes_leve_exception(
    service: MultiIndicateursService,
    indicateurs_mock: dict[str, Indicateur],
):
    """Vérifie l'interdiction de comparer une série trimestrielle (Q) et annuelle (A)."""
    # GIVEN
    selections = [
        Selection(indicateur="A", pays="FRA", classif1="Total"),
        Selection(indicateur="C", pays="FRA", classif1="Total"),
    ]

    with patch.object(
        IndicateurDAO,
        "trouver_par_code",
        side_effect=[indicateurs_mock["EMP"], indicateurs_mock["ANNUEL"]],
    ):
        # WHEN / THEN
        with pytest.raises(ValueError, match="fréquences différentes"):
            service.comparer(selections)


def test_indicateur_inconnu_leve_exception(service: MultiIndicateursService):
    """Vérifie le rejet explicite en cas de code d'indicateur inexistant."""
    # GIVEN
    selections = [
        Selection(indicateur="CODE_INEXISTANT", pays="FRA", classif1="Total"),
        Selection(indicateur="B", pays="FRA", classif1="Total"),
    ]

    with patch.object(IndicateurDAO, "trouver_par_code", return_value=None):
        # WHEN / THEN
        with pytest.raises(ValueError, match="Indicateur inconnu"):
            service.comparer(selections)