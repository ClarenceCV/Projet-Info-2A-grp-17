"""Tests unitaires pour la fonctionnalité FO3 (RapportService)."""

from unittest.mock import patch

import pandas as pd
import pytest

from service.rapport_service import RapportService


@pytest.fixture
def sample_evolution_df() -> pd.DataFrame:
    """Fixture d'un DataFrame d'évolution synthétique."""
    return pd.DataFrame([
        {"code_iso": "FRA", "nom_pays": "France", "periode": "2023Q1", "valeur": 100.0},
        {"code_iso": "FRA", "nom_pays": "France", "periode": "2023Q2", "valeur": 105.0},
        {"code_iso": "DEU", "nom_pays": "Allemagne", "periode": "2023Q1", "valeur": 200.0},
        {"code_iso": "DEU", "nom_pays": "Allemagne", "periode": "2023Q2", "valeur": 195.0},
    ])


@pytest.fixture
def sample_comparaison_df() -> pd.DataFrame:
    """Fixture d'un DataFrame de comparaison synthétique."""
    return pd.DataFrame([
        {"code_iso": "FRA", "nom_pays": "France", "valeur": 105.0},
        {"code_iso": "DEU", "nom_pays": "Allemagne", "valeur": 195.0},
    ])


def test_resume_statistique(sample_evolution_df):
    service = RapportService()
    stats = service.resume_statistique(sample_evolution_df)

    assert "FRA" in stats
    assert stats["FRA"]["min"] == 100.0
    assert stats["FRA"]["max"] == 105.0
    assert stats["FRA"]["moyenne"] == 102.5
    assert stats["FRA"]["evolution"] == 5.0

    assert "DEU" in stats
    assert stats["DEU"]["evolution"] == -5.0


def test_conclusion(sample_evolution_df, sample_comparaison_df):
    service = RapportService()
    stats = service.resume_statistique(sample_evolution_df)
    conclusion_txt = service.conclusion(stats, sample_comparaison_df)

    assert "France" in conclusion_txt
    assert "Allemagne" in conclusion_txt
    assert "valeur la plus elevee" in conclusion_txt


def test_generer_pdf_retourne_octets_valides(sample_evolution_df, sample_comparaison_df):
    service = RapportService()

    with patch("service.evolution_service.EvolutionService.evolution", return_value=sample_evolution_df), \
         patch("service.comparaison_pays_service.ComparaisonPaysService.comparer_pays", return_value=sample_comparaison_df):

        pdf_bytes = service.generer(
            code_indicateur="IND_TEST",
            pays=["FRA", "DEU"],
            classif1="Total",
        )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
