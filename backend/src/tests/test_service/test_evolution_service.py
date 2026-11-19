"""
Tests du service F3 (évolution dans le temps).
Le DAO est remplacé par un faux (patch.object) qui renvoie un petit DataFrame écrit à la main :
les tests ne dépendent ni de la base ni d'ILOSTAT, et on connaît le résultat attendu.

Lancement (depuis backend/src) :
     uv run python -m pytest
"""

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
    """
    Vérifie le calcul des variations d'une période à la suivante :
    pour la série 50 -> 51 -> 53, la variation absolue vaut +1 puis +2,
    et la variation en pourcentage vaut 2 % puis (2 / 51) * 100.
    """
    # WHEN
    res = evolution_avec(faux_df())
    # THEN : 50 -> 51 -> 53
    assert list(res["variation_abs"])[1:] == [1.0, 2.0]
    assert list(res["variation_pct"])[1:] == [2.0, (2.0 / 51.0) * 100]


def test_premiere_periode_sans_variation():
    """
    Vérifie que la première période d'une série n'a pas de variation
    (variation_abs et variation_pct valent NaN), faute de période précédente.
    """
    res = evolution_avec(faux_df())
    assert np.isnan(res.loc[0, "variation_abs"])
    assert np.isnan(res.loc[0, "variation_pct"])


def test_evolution_renvoie_les_bonnes_colonnes():
    """
    Vérifie que le DataFrame retourné contient exactement les colonnes
    de COLONNES_EVOLUTION, dans cet ordre.
    """
    res = evolution_avec(faux_df())
    assert list(res.columns) == COLONNES_EVOLUTION


def test_evolution_garde_les_n_dernieres_periodes():
    """
    Vérifie que `n_periodes` limite le résultat aux n périodes les plus
    récentes (ici 2024Q2 et 2024Q3), et que les variations sont calculées
    avant la coupe : 2024Q2 conserve donc sa variation par rapport à 2024Q1.
    """
    # WHEN
    res = evolution_avec(faux_df(), n_periodes=2)
    # THEN : 2024Q2 et 2024Q3, et 2024Q2 a bien une variation (calculée avant de couper)
    assert list(res["periode"]) == ["2024Q2", "2024Q3"]
    assert res.loc[0, "variation_abs"] == 1.0


def test_evolution_n_periodes_superieur_au_nombre_de_periodes():
    """
    Vérifie que si `n_periodes` dépasse le nombre de périodes disponibles
    (40 > 3), aucune erreur n'est levée et toutes les périodes sont renvoyées.
    """
    res = evolution_avec(faux_df(), n_periodes=40)
    assert len(res) == 3


def test_evolution_deux_pays_sans_debordement():
    """
    Vérifie que les variations sont calculées séparément pour chaque pays :
    la première période de l'Espagne n'est pas comparée à la dernière de la
    France (elle vaut NaN) et les variations suivantes sont celles de l'Espagne
    seule (+1 puis +3). Le résultat contient bien 6 lignes (3 par pays).
    """
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
    """
    Vérifie que `n_periodes` est appliqué pour chaque pays et non globalement :
    avec n_periodes=2, la France (3 périodes) et l'Espagne (2 périodes)
    ont chacune 2 lignes dans le résultat.
    """
    df = pd.concat([
        faux_df("FRA", "France"),
        faux_df("ESP", "Espagne", periodes=("2024Q2", "2024Q3"), valeurs=(41.0, 44.0)),
    ])
    res = evolution_avec(df, pays=("FRA", "ESP"), n_periodes=2)
    assert list(res.groupby("code_iso").size()) == [2, 2]


def test_evolution_une_seule_source_par_periode():
    """
    Vérifie que, lorsque plusieurs sources existent pour une même période,
    une seule ligne par période est conservée : celle de la première source
    par ordre alphabétique ("A - LFS"), ce qui donne ici 99.0 pour 2024Q2.
    """
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
    """
    Vérifie que les périodes sont triées par ordre chronologique même si le
    DAO les renvoie dans le désordre, et que les variations sont calculées
    dans cet ordre trié (+1 puis +2).
    """
    # GIVEN : périodes dans le désordre
    df = faux_df(periodes=("2024Q3", "2024Q1", "2024Q2"), valeurs=(53.0, 50.0, 51.0))
    res = evolution_avec(df)
    assert list(res["periode"]) == ["2024Q1", "2024Q2", "2024Q3"]
    assert list(res["variation_abs"])[1:] == [1.0, 2.0]


def test_evolution_valeur_precedente_nulle_pas_de_pourcentage_infini():
    """
    Vérifie le cas d'une valeur précédente égale à 0 : la variation absolue
    est calculée normalement (+5), mais la variation en pourcentage vaut NaN
    au lieu de l'infini (inf n'est pas valide en JSON). La période suivante
    (5 -> 10) donne bien +100 %.
    """
    # GIVEN : 0 -> 5 : variation_abs = 5, mais le % n'est pas défini (pas de inf, invalide en JSON)
    res = evolution_avec(faux_df(valeurs=(0.0, 5.0, 10.0)))
    assert res.loc[1, "variation_abs"] == 5.0
    assert np.isnan(res.loc[1, "variation_pct"])
    assert res.loc[2, "variation_pct"] == 100.0


def test_evolution_dao_vide():
    """
    Vérifie que, lorsque le DAO ne renvoie aucune donnée, le service ne
    plante pas : le résultat est un DataFrame vide qui conserve néanmoins
    les colonnes de COLONNES_EVOLUTION.
    """
    # GIVEN : le DAO ne trouve rien
    vide = pd.DataFrame(columns=faux_df().columns)
    # WHEN
    res = evolution_avec(vide)
    # THEN : pas d'erreur, résultat vide avec les bonnes colonnes
    assert res.empty
    assert list(res.columns) == COLONNES_EVOLUTION
