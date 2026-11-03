# Tests de EvolutionService (F3). Le DAO est remplacé par un faux : pas de base de données.

from unittest.mock import patch

import numpy as np
import pandas as pd

from dao.observation_dao import ObservationDAO
from service.evolution_service import COLONNES_EVOLUTION, EvolutionService


def faux_df(code_iso="FRA", nom="France", periodes=("2024Q1", "2024Q2", "2024Q3"),
            valeurs=(50.0, 51.0, 53.0), source="LFS"):
    """Un petit DataFrame au format renvoyé par ObservationDAO.lire (un pays, une source)"""
    n = len(periodes)
    return pd.DataFrame({
        "indicateur": ["X"] * n,
        "code_iso": [code_iso] * n,
        "nom_pays": [nom] * n,
        "source": [source] * n,
        "periode": list(periodes),
        "sexe": ["Total"] * n,
        "classif1": ["15+"] * n,
        "valeur": list(valeurs),
        "unite": ["%"] * n,
        "statut": [None] * n,
    })


def evolution_avec(df, pays=("FRA",), n_periodes=8):
    """Appelle le service avec un DAO factice qui renvoie df"""
    with patch.object(ObservationDAO, "lire", return_value=df):
        return EvolutionService().evolution("X", list(pays), classif1="15+", n_periodes=n_periodes)


def test_evolution_calcule_les_variations():
    # WHEN
    res = evolution_avec(faux_df())
    # THEN : 50 -> 51 -> 53
    assert list(res["variation_abs"])[1:] == [1.0, 2.0]
    assert list(res["variation_pct"])[1:] == [2.0, (2.0 / 51.0) * 100]


def test_premiere_periode_sans_variation():
    res = evolution_avec(faux_df())
    assert np.isnan(res.loc[0, "variation_abs"])
    assert np.isnan(res.loc[0, "variation_pct"])


def test_evolution_renvoie_les_bonnes_colonnes():
    res = evolution_avec(faux_df())
    assert list(res.columns) == COLONNES_EVOLUTION


def test_evolution_garde_les_n_dernieres_periodes():
    # WHEN
    res = evolution_avec(faux_df(), n_periodes=2)
    # THEN : 2024Q2 et 2024Q3, et 2024Q2 a bien une variation (calculée avant de couper)
    assert list(res["periode"]) == ["2024Q2", "2024Q3"]
    assert res.loc[0, "variation_abs"] == 1.0


def test_evolution_n_periodes_superieur_au_nombre_de_periodes():
    res = evolution_avec(faux_df(), n_periodes=40)
    assert len(res) == 3


def test_evolution_deux_pays_sans_debordement():
    # GIVEN : FRA et ESP ; la 1re période d'ESP ne doit pas être comparée à la dernière de FRA
    df = pd.concat([
        faux_df("FRA", "France", valeurs=(50.0, 51.0, 53.0)),
        faux_df("ESP", "Espagne", valeurs=(40.0, 41.0, 44.0)),
    ])
    # WHEN
    res = evolution_avec(df, pays=("FRA", "ESP"))
    # THEN
    esp = res[res["code_iso"] == "ESP"].reset_index(drop=True)
    assert np.isnan(esp.loc[0, "variation_abs"])
    assert list(esp["variation_abs"])[1:] == [1.0, 3.0]
    assert len(res) == 6


def test_evolution_n_periodes_s_applique_par_pays():
    df = pd.concat([
        faux_df("FRA", "France"),
        faux_df("ESP", "Espagne", periodes=("2024Q2", "2024Q3"), valeurs=(41.0, 44.0)),
    ])
    res = evolution_avec(df, pays=("FRA", "ESP"), n_periodes=2)
    assert list(res.groupby("code_iso").size()) == [2, 2]


def test_evolution_une_seule_source_par_periode():
    # GIVEN : 2 sources pour 2024Q2 ; on garde la première par ordre alphabétique ("A - ...")
    df = pd.concat([
        faux_df(source="B - Autre enquête"),
        faux_df(periodes=("2024Q2",), valeurs=(99.0,), source="A - LFS"),
    ])
    # WHEN
    res = evolution_avec(df)
    # THEN : une ligne par période, et la valeur de la source A pour 2024Q2
    assert list(res["periode"]) == ["2024Q1", "2024Q2", "2024Q3"]
    assert res.loc[res["periode"] == "2024Q2", "valeur"].iloc[0] == 99.0


def test_evolution_tri_chronologique():
    # GIVEN : périodes dans le désordre
    df = faux_df(periodes=("2024Q3", "2024Q1", "2024Q2"), valeurs=(53.0, 50.0, 51.0))
    res = evolution_avec(df)
    assert list(res["periode"]) == ["2024Q1", "2024Q2", "2024Q3"]
    assert list(res["variation_abs"])[1:] == [1.0, 2.0]


def test_evolution_valeur_precedente_nulle_pas_de_pourcentage_infini():
    # GIVEN : 0 -> 5 : variation_abs = 5, mais le % n'est pas défini (pas de inf, invalide en JSON)
    res = evolution_avec(faux_df(valeurs=(0.0, 5.0, 10.0)))
    assert res.loc[1, "variation_abs"] == 5.0
    assert np.isnan(res.loc[1, "variation_pct"])
    assert res.loc[2, "variation_pct"] == 100.0


def test_evolution_dao_vide():
    # GIVEN : le DAO ne trouve rien
    vide = pd.DataFrame(columns=faux_df().columns)
    # WHEN
    res = evolution_avec(vide)
    # THEN : pas d'erreur, résultat vide avec les bonnes colonnes
    assert res.empty
    assert list(res.columns) == COLONNES_EVOLUTION