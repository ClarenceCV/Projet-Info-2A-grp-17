import pandas as pd
import pytest
from unittest.mock import patch, Mock

from fetcher.fetcher import (
    URL_ILOSTAT,
    construire_url,
    load_data,
    get_columns_info,
    filter_columns,
)


# ============================================================
# TESTS DE CONSTRUIRE_URL
# ============================================================

def test_construire_url():
    """Vérifie la construction de l'URL avec les paramètres par défaut."""

    url = construire_url("EMP_5EMP_SEX_OC2_NB_Q")

    assert url == (
        f"{URL_ILOSTAT}?id=EMP_5EMP_SEX_OC2_NB_Q"
        "&timefrom=2020&type=both&format=.csv"
    )


def test_construire_url_annee_personnalisee():
    """Vérifie la construction de l'URL avec une année personnalisée."""

    url = construire_url("EMP_5EMP_SEX_OC2_NB_Q", annee_debut=2015)

    assert "timefrom=2015" in url
    assert "id=EMP_5EMP_SEX_OC2_NB_Q" in url


# ============================================================
# TESTS DE LOAD_DATA
# ============================================================

@patch("fetcher.fetcher.requests.get")
def test_load_data(mock_get):
    """Vérifie le téléchargement et la conversion en DataFrame."""

    # Simulation d'une réponse HTTP
    mock_response = Mock()
    mock_response.text = (
        "ref_area,time,obs_value\n"
        "FRA,2020,1000\n"
        "DEU,2020,2000\n"
    )

    mock_get.return_value = mock_response

    df = load_data("https://test.fr/data.csv")

    # Vérification de l'appel HTTP
    mock_get.assert_called_once_with(
        "https://test.fr/data.csv",
        timeout=300
    )

    # Vérification du DataFrame
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["ref_area", "time", "obs_value"]
    assert df.iloc[0]["ref_area"] == "FRA"


@patch("fetcher.fetcher.requests.get")
def test_load_data_erreur_http(mock_get):
    """Vérifie qu'une erreur HTTP est correctement remontée."""

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = (
        Exception("Erreur HTTP")
    )

    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="Erreur HTTP"):
        load_data("https://test.fr/data.csv")


@patch("fetcher.fetcher.requests.get")
def test_load_data_reponse_vide(mock_get):
    """Vérifie le comportement lorsque l'API renvoie une réponse vide."""

    mock_response = Mock()
    mock_response.text = "   "

    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="réponse vide"):
        load_data("https://test.fr/data.csv")


# ============================================================
# TESTS DE GET_COLUMNS_INFO
# ============================================================

def test_get_columns_info(capsys):
    """Vérifie les informations affichées sur le DataFrame."""

    df = pd.DataFrame({
        "ref_area": ["FRA", "DEU", "FRA"],
        "time": [2020, 2020, 2021],
        "obs_value": [100, 200, 300]
    })

    colonnes = get_columns_info(df)

    # Vérification de la liste retournée
    assert colonnes == ["ref_area", "time", "obs_value"]

    # Vérification des affichages
    captured = capsys.readouterr()

    assert "Nombre de colonnes : 3" in captured.out
    assert "Nombre de lignes : 3" in captured.out
    assert "ref_area" in captured.out
    assert "valeurs uniques" in captured.out
    assert "FRA" in captured.out


def test_get_columns_info_valeurs_vides(capsys):
    """Vérifie le comportement avec une colonne entièrement vide."""

    df = pd.DataFrame({
        "ref_area": [None, None],
        "time": [2020, 2021]
    })

    colonnes = get_columns_info(df)

    captured = capsys.readouterr()

    assert colonnes == ["ref_area", "time"]
    assert "exemple: None" in captured.out


# ============================================================
# TESTS DE FILTER_COLUMNS
# ============================================================

def test_filter_columns():
    """Vérifie la sélection des colonnes sans renommage."""

    df = pd.DataFrame({
        "ref_area": ["FRA", "DEU"],
        "time": [2020, 2021],
        "obs_value": [100, 200],
        "sex": ["Male", "Female"]
    })

    resultat = filter_columns(
        df,
        colonnes_a_garder=["ref_area", "obs_value"]
    )

    assert list(resultat.columns) == ["ref_area", "obs_value"]
    assert len(resultat) == 2
    assert resultat.iloc[0]["ref_area"] == "FRA"


def test_filter_columns_avec_renommage():
    """Vérifie la sélection et le renommage des colonnes."""

    df = pd.DataFrame({
        "ref_area.label": ["France", "Germany"],
        "time": [2020, 2021],
        "obs_value": [100, 200]
    })

    resultat = filter_columns(
        df,
        colonnes_a_garder=[
            "ref_area.label",
            "obs_value"
        ],
        renommage=[
            "pays",
            "valeur"
        ]
    )

    assert list(resultat.columns) == ["pays", "valeur"]
    assert resultat.iloc[0]["pays"] == "France"
    assert resultat.iloc[1]["valeur"] == 200


def test_filter_columns_colonne_absente(capsys):
    """Vérifie le comportement lorsqu'une colonne demandée est absente."""

    df = pd.DataFrame({
        "ref_area": ["FRA"],
        "time": [2020]
    })

    resultat = filter_columns(
        df,
        colonnes_a_garder=["ref_area", "obs_value"]
    )

    captured = capsys.readouterr()

    assert list(resultat.columns) == ["ref_area"]
    assert "Attention, colonnes absentes" in captured.out
    assert "obs_value" in captured.out


def test_filter_columns_renommage_longueur_incorrecte():
    """Vérifie qu'une erreur est levée si les longueurs diffèrent."""

    df = pd.DataFrame({
        "ref_area": ["FRA"],
        "time": [2020]
    })

    with pytest.raises(ValueError, match="doit avoir la même longueur"):

        filter_columns(
            df,
            colonnes_a_garder=["ref_area", "time"],
            renommage=["pays"]
        )
