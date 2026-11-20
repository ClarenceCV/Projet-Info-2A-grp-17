"""
Tests du service de rapport (FO3).
Les services d'évolution et de comparaison sont remplacés par des faux (patch)
qui renvoient de petits DataFrames écrits à la main : les tests ne dépendent
ni de la base ni d'ILOSTAT, et on connaît le résultat attendu.

Lancement (depuis le dossier backend) :
     uv run pytest src/tests
"""

from unittest.mock import patch

import pandas as pd
import pytest

from service.rapport_service import RapportService


@pytest.fixture(name="sample_evolution_df")
def fixture_sample_evolution_df() -> pd.DataFrame:
    """Fixture d'un DataFrame d'évolution synthétique."""
    return pd.DataFrame([
        {"code_iso": "FRA", "nom_pays": "France", "periode": "2023Q1", "valeur": 100.0},
        {"code_iso": "FRA", "nom_pays": "France", "periode": "2023Q2", "valeur": 105.0},
        {"code_iso": "DEU", "nom_pays": "Allemagne", "periode": "2023Q1", "valeur": 200.0},
        {"code_iso": "DEU", "nom_pays": "Allemagne", "periode": "2023Q2", "valeur": 195.0},
    ])


@pytest.fixture(name="sample_comparaison_df")
def fixture_sample_comparaison_df() -> dict:
    """
    Fixture d'une comparaison synthétique, au même format que ComparaisonPaysService.comparer_pays :
    un dictionnaire {"periode_reference", "classement", "plus_hauts", "plus_bas"}.
    """
    classement = pd.DataFrame(
        [
            {
                "rang": 1,
                "code_iso": "DEU",
                "nom_pays": "Allemagne",
                "periode": "2023Q2",
                "valeur": 195.0,
                "unite": "%",
            },
            {
                "rang": 2,
                "code_iso": "FRA",
                "nom_pays": "France",
                "periode": "2023Q2",
                "valeur": 105.0,
                "unite": "%",
            },
        ]
    )
    return {
        "periode_reference": "2023Q2",
        "classement": classement,
        "plus_hauts": classement.head(1),
        "plus_bas": classement.tail(1),
    }


def test_resume_statistique(sample_evolution_df):
    """
    Vérifie que `resume_statistique` calcule, pour chaque pays, le minimum,
    le maximum, la moyenne et l'évolution entre la première et la dernière
    période : la France (100 -> 105) a une évolution de +5.0 et une moyenne
    de 102.5, l'Allemagne (200 -> 195) une évolution de -5.0.
    """
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
    """
    Vérifie que le texte de conclusion généré à partir des statistiques et
    de la comparaison mentionne les deux pays (France et Allemagne) ainsi
    que l'expression "valeur la plus elevee".
    """
    service = RapportService()
    stats = service.resume_statistique(sample_evolution_df)
    conclusion_txt = service.conclusion(stats, sample_comparaison_df)

    assert "France" in conclusion_txt
    assert "Allemagne" in conclusion_txt
    assert "valeur la plus elevee" in conclusion_txt
    assert (
        "Pour la periode de reference 2023Q2, Allemagne presente la valeur la plus elevee"
        in conclusion_txt
    )


def test_conclusion_classement_vide(sample_evolution_df):
    # comparer_pays renvoie un classement vide quand il n'y a pas de données : pas de phrase de
    # classement
    service = RapportService()
    stats = service.resume_statistique(sample_evolution_df)
    comparaison_vide = {
        "periode_reference": None,
        "classement": pd.DataFrame(columns=["code_iso", "valeur"]),
    }

    conclusion_txt = service.conclusion(stats, comparaison_vide)

    assert "France" in conclusion_txt
    assert "valeur la plus elevee" not in conclusion_txt


def test_conclusion_sans_donnees():
    assert (
        RapportService().conclusion({}, {})
        == "Aucune donnee disponible pour etablir une conclusion."
    )


def test_generer_pdf_retourne_octets_valides(sample_evolution_df, sample_comparaison_df):
    """
    Vérifie que `generer` produit un rapport PDF sans erreur, les services
    d'évolution et de comparaison étant remplacés par des faux qui renvoient
    des DataFrames synthétiques (pas de base de données).
    """
    service = RapportService()

    with patch(
        "service.evolution_service.EvolutionService.evolution", return_value=sample_evolution_df
        ), \
            patch(
            "service.comparaison_pays_service.ComparaisonPaysService.comparer_pays", 
            return_value=sample_comparaison_df
            ):

        pdf_bytes = service.generer(
            code_indicateur="IND_TEST",
            pays=["FRA", "DEU"],
            classif1="Total",
        )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
