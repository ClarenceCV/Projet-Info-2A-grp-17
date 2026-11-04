
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from business_object.indicateur import Indicateur
from fetcher.data_processing import DataProcessing


# ---------------------------------------------------------
# Données de test
# ---------------------------------------------------------

@pytest.fixture
def processing():
    return DataProcessing()


@pytest.fixture
def df_brut():
    return pd.DataFrame({
        "ref_area": ["FRA", "DEU", "FRA"],
        "ref_area.label": ["France", "Germany", "France"],
        "source": ["ILO", "ILO", "ILO"],
        "source.label": ["Source ILO", "Source ILO", "Source ILO"],
        "time": [2023, 2023, 2024],
        "sex.label": ["Sex: Female", "Sex: Male", "Sex: Female"],
        "classif1.label": [
            "Age: 15-24",
            "Age: 25-64",
            "Age: 15-24"
        ],
        "obs_value": ["12.5", "20.0", "15.0"],
        "obs_status": ["A", None, "A"]
    })


# ---------------------------------------------------------
# Tests du constructeur
# ---------------------------------------------------------

def test_init(processing):
    assert processing.url_API == "https://rplumber.ilo.org/data/indicator"


# ---------------------------------------------------------
# Tests de fetch_data
# ---------------------------------------------------------

@patch("fetcher.data_processing.load_data")
@patch("fetcher.data_processing.time.sleep")
def test_fetch_data_succes(mock_sleep, mock_load_data, processing):
    """Les données de chaque pays sont téléchargées puis réunies."""
    df_france = pd.DataFrame({"ref_area": ["FRA"], "obs_value": [10]})
    df_allemagne = pd.DataFrame({"ref_area": ["DEU"], "obs_value": [20]})

    mock_load_data.side_effect = [df_france, df_allemagne]

    with patch("fetcher.data_processing.PAYS_SUIVIS", ["FRA", "DEU"]):
        resultat = processing.fetch_data("INDICATEUR_TEST")

    assert len(resultat) == 2
    assert list(resultat["ref_area"]) == ["FRA", "DEU"]
    assert mock_load_data.call_count == 2
    mock_sleep.assert_not_called()


@patch("fetcher.data_processing.load_data")
@patch("fetcher.data_processing.time.sleep")
def test_fetch_data_reessaye_apres_echec(
    mock_sleep, mock_load_data, processing
):
    """Un pays est téléchargé une seconde fois après un échec."""
    df_france = pd.DataFrame({"ref_area": ["FRA"], "obs_value": [10]})

    mock_load_data.side_effect = [
        Exception("Erreur API"),
        df_france
    ]

    with patch("fetcher.data_processing.PAYS_SUIVIS", ["FRA"]):
        resultat = processing.fetch_data("INDICATEUR_TEST")

    assert len(resultat) == 1
    assert mock_load_data.call_count == 2
    mock_sleep.assert_called_once_with(3)


@patch("fetcher.data_processing.load_data")
@patch("fetcher.data_processing.time.sleep")
def test_fetch_data_ignore_pays_apres_deux_echecs(
    mock_sleep, mock_load_data, processing
):
    """Un pays est ignoré si les deux tentatives échouent."""
    mock_load_data.side_effect = Exception("API indisponible")

    with patch("fetcher.data_processing.PAYS_SUIVIS", ["FRA"]):
        resultat = processing.fetch_data("INDICATEUR_TEST")

    assert resultat.empty
    assert mock_load_data.call_count == 2
    mock_sleep.assert_called_once_with(3)


@patch("fetcher.data_processing.load_data")
def test_fetch_data_ignore_dataframe_vide(
    mock_load_data, processing
):
    """Les DataFrames vides ne sont pas ajoutés au résultat."""
    mock_load_data.return_value = pd.DataFrame()

    with patch("fetcher.data_processing.PAYS_SUIVIS", ["FRA"]):
        resultat = processing.fetch_data("INDICATEUR_TEST")

    assert resultat.empty


@patch("fetcher.data_processing.load_data")
def test_fetch_data_aucun_pays(mock_load_data, processing):
    """Aucun téléchargement si aucun pays n'est configuré."""
    with patch("fetcher.data_processing.PAYS_SUIVIS", []):
        resultat = processing.fetch_data("INDICATEUR_TEST")

    assert resultat.empty
    mock_load_data.assert_not_called()


# ---------------------------------------------------------
# Tests de parse_data
# ---------------------------------------------------------

def test_parse_data_dataframe_vide(processing):
    resultat = processing.parse_data(pd.DataFrame())

    assert resultat.empty
    assert list(resultat.columns) == [
        "code_iso", "nom_pays", "source", "periode",
        "sexe", "classif1", "valeur", "statut"
    ]


def test_parse_data_selection_renommage_et_nettoyage(
    processing, df_brut
):
    resultat = processing.parse_data(df_brut)

    assert len(resultat) == 3
    assert list(resultat.columns) == [
        "code_iso", "nom_pays", "source", "periode",
        "sexe", "classif1", "valeur", "statut"
    ]

    assert resultat.loc[0, "code_iso"] == "FRA"
    assert resultat.loc[0, "nom_pays"] == "France"
    assert resultat.loc[0, "source"] == "Source ILO"
    assert resultat.loc[0, "sexe"] == "Female"
    assert resultat.loc[0, "classif1"] == "15-24"
    assert resultat.loc[0, "valeur"] == 12.5


def test_parse_data_supprime_valeurs_invalides(processing, df_brut):
    df_brut.loc[0, "obs_value"] = "texte"
    df_brut.loc[1, "obs_value"] = None

    resultat = processing.parse_data(df_brut)

    assert len(resultat) == 1
    assert resultat.iloc[0]["code_iso"] == "FRA"


def test_parse_data_colonnes_optionnelles_absentes(processing):
    """classif1.label et obs_status peuvent être absentes."""
    df = pd.DataFrame({
        "ref_area": ["FRA"],
        "ref_area.label": ["France"],
        "source": ["ILO"],
        "source.label": ["Source ILO"],
        "time": [2023],
        "sex.label": ["Sex: Female"],
        "obs_value": [12.5]
    })

    resultat = processing.parse_data(df)

    assert len(resultat) == 1
    assert resultat.loc[0, "classif1"] == "_NA"
    assert pd.isna(resultat.loc[0, "statut"])


def test_parse_data_supprime_doublons(processing):
    df = pd.DataFrame({
        "ref_area": ["FRA", "FRA"],
        "ref_area.label": ["France", "France"],
        "source": ["ILO", "ILO"],
        "source.label": ["Source ILO", "Source ILO"],
        "time": [2023, 2023],
        "sex.label": ["Sex: Female", "Sex: Female"],
        "classif1.label": ["Age: 15-24", "Age: 15-24"],
        "obs_value": [12.5, 99.0],
        "obs_status": ["A", "A"]
    })

    resultat = processing.parse_data(df)

    assert len(resultat) == 1
    # La première ligne est conservée.
    assert resultat.loc[0, "valeur"] == 12.5


def test_parse_data_remplace_statut_nan_par_none(processing):
    df = pd.DataFrame({
        "ref_area": ["FRA"],
        "ref_area.label": ["France"],
        "source": ["ILO"],
        "source.label": ["Source ILO"],
        "time": [2023],
        "sex.label": ["Sex: Female"],
        "classif1.label": ["Age: 15-24"],
        "obs_value": [12.5],
        "obs_status": [float("nan")]
    })

    resultat = processing.parse_data(df)

    assert resultat.loc[0, "statut"] is None


# ---------------------------------------------------------
# Tests de save_data
# ---------------------------------------------------------

@patch("fetcher.data_processing.ObservationDAO")
@patch("fetcher.data_processing.PaysDAO")
@patch("fetcher.data_processing.IndicateurDAO")
def test_save_data(
    mock_indicateur_dao,
    mock_pays_dao,
    mock_observation_dao,
    processing
):
    """Les trois DAO sont appelés dans le bon ordre."""
    indicateur = MagicMock(spec=Indicateur)
    df = pd.DataFrame({
        "code_iso": ["FRA"],
        "nom_pays": ["France"],
        "source": ["Source ILO"],
        "periode": [2023],
        "sexe": ["Female"],
        "classif1": ["15-24"],
        "valeur": [12.5],
        "statut": ["A"]
    })

    mock_indicateur_dao.return_value.enregistrer.return_value = 42
    mock_observation_dao.return_value.enregistrer.return_value = 1

    resultat = processing.save_data(indicateur, df)

    assert resultat == 1

    mock_indicateur_dao.return_value.enregistrer.assert_called_once_with(
        indicateur
    )
    mock_pays_dao.return_value.enregistrer.assert_called_once()

    pays_envoyes = (
        mock_pays_dao.return_value.enregistrer.call_args[0][0]
    )
    assert list(pays_envoyes.columns) == ["code_iso", "nom_pays"]

    mock_observation_dao.return_value.enregistrer.assert_called_once()
    args = mock_observation_dao.return_value.enregistrer.call_args[0]
    assert args[0] == 42
    pd.testing.assert_frame_equal(args[1], df)


# ---------------------------------------------------------
# Tests de charger
# ---------------------------------------------------------

@patch.object(DataProcessing, "save_data", return_value=2)
@patch.object(DataProcessing, "parse_data")
@patch.object(DataProcessing, "fetch_data")
def test_charger_un_indicateur(
    mock_fetch, mock_parse, mock_save, processing
):
    indicateur = MagicMock(spec=Indicateur)
    indicateur.code = "INDICATEUR_TEST"

    df_brut = pd.DataFrame({"brut": [1, 2]})
    df_propre = pd.DataFrame({"propre": [1, 2]})

    mock_fetch.return_value = df_brut
    mock_parse.return_value = df_propre

    resultat = processing.charger([indicateur])

    assert resultat == 2
    mock_fetch.assert_called_once_with("INDICATEUR_TEST")
    mock_parse.assert_called_once_with(df_brut)
    mock_save.assert_called_once_with(indicateur, df_propre)


@patch.object(DataProcessing, "save_data", return_value=3)
@patch.object(DataProcessing, "parse_data")
@patch.object(DataProcessing, "fetch_data")
def test_charger_plusieurs_indicateurs(
    mock_fetch, mock_parse, mock_save, processing
):
    indicateur1 = MagicMock(spec=Indicateur)
    indicateur1.code = "INDICATEUR_1"

    indicateur2 = MagicMock(spec=Indicateur)
    indicateur2.code = "INDICATEUR_2"

    mock_fetch.return_value = pd.DataFrame()
    mock_parse.return_value = pd.DataFrame()

    resultat = processing.charger([indicateur1, indicateur2])

    assert resultat == 6
    assert mock_fetch.call_count == 2
    assert mock_parse.call_count == 2
    assert mock_save.call_count == 2


@patch.object(DataProcessing, "save_data")
@patch.object(DataProcessing, "parse_data")
@patch.object(DataProcessing, "fetch_data")
def test_charger_continue_si_un_indicateur_echoue(
    mock_fetch, mock_parse, mock_save, processing
):
    """L'échec d'un indicateur ne bloque pas les suivants."""
    indicateur1 = MagicMock(spec=Indicateur)
    indicateur1.code = "INDICATEUR_1"

    indicateur2 = MagicMock(spec=Indicateur)
    indicateur2.code = "INDICATEUR_2"

    mock_fetch.side_effect = [
        Exception("Erreur API"),
        pd.DataFrame({"brut": [1]})
    ]
    mock_parse.return_value = pd.DataFrame({"propre": [1]})
    mock_save.return_value = 4

    resultat = processing.charger([indicateur1, indicateur2])

    assert resultat == 4
    assert mock_fetch.call_count == 2
    mock_save.assert_called_once_with(
        indicateur2,
        mock_parse.return_value
    )


def test_charger_liste_vide(processing):
    resultat = processing.charger([])

    assert resultat == 0
