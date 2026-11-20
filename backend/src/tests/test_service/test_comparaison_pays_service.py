"""
Tests du service F4 (comparaison entre pays).
Le DAO est remplacé par un faux (patch.object) qui renvoie un petit DataFrame écrit à la main :
les tests ne dépendent ni de la base ni d'ILOSTAT, et on connaît le résultat attendu.

Lancement (depuis backend/src) :
     uv run python -m pytest
"""

from unittest.mock import patch

import pandas as pd

from dao.observation_dao import ObservationDAO
from service.comparaison_pays_service import ComparaisonPaysService


def faux_df():
    """3 pays ; l'Espagne s'arrête un trimestre plus tôt"""
    return pd.DataFrame({
        "code_iso": ["FRA", "FRA", "DEU", "DEU", "ESP"],
        "nom_pays": ["France", "France", "Germany", "Germany", "Spain"],
        "source": ["LFS"] * 5,
        "periode": ["2024Q3", "2024Q4", "2024Q3", "2024Q4", "2024Q3"],
        "valeur": [50.0, 52.0, 60.0, 61.0, 45.0],
        "unite": ["%"] * 5,
    })


def test_classement_par_valeur_decroissante():
    """
    Vérifie que le classement est trié par valeur décroissante
    et que les rangs sont attribués de 1 à n dans cet ordre
    (Allemagne 61.0, France 52.0, Espagne 45.0).
    """
    # GIVEN
    with patch.object(ObservationDAO, "lire", return_value=faux_df()):
        # WHEN
        res = ComparaisonPaysService().comparer_pays("X", classif1="15+")
    # THEN
    assert list(res["classement"]["code_iso"]) == ["DEU", "FRA", "ESP"]
    assert list(res["classement"]["rang"]) == [1, 2, 3]


def test_garde_la_derniere_periode_de_chaque_pays():
    """
    Vérifie que seule la dernière période disponible de chaque pays est
    conservée dans le classement : la France garde 2024Q4 (et non 2024Q3),
    l'Espagne garde sa propre dernière période (2024Q3), et la période de
    référence retournée est la plus récente de toutes (2024Q4).
    """
    # GIVEN
    with patch.object(ObservationDAO, "lire", return_value=faux_df()):
        # WHEN
        res = ComparaisonPaysService().comparer_pays("X", classif1="15+")
    # THEN
    classement = res["classement"]
    france = classement[classement["code_iso"] == "FRA"]
    assert list(france["valeur"]) == [52.0]       # 2024Q4, pas 50.0 (2024Q3)
    assert list(france["periode"]) == ["2024Q4"]
    espagne = classement[classement["code_iso"] == "ESP"]
    assert list(espagne["periode"]) == ["2024Q3"]  # sa dernière période à elle
    assert res["periode_reference"] == "2024Q4"


def test_plus_hauts_et_plus_bas():
    """
    Vérifie que, avec top=1, `plus_hauts` contient uniquement le pays à la
    valeur la plus élevée (Allemagne) et `plus_bas` uniquement celui à la
    valeur la plus faible (Espagne).
    """
    # GIVEN
    with patch.object(ObservationDAO, "lire", return_value=faux_df()):
        # WHEN
        res = ComparaisonPaysService().comparer_pays("X", classif1="15+", top=1)
    # THEN
    assert list(res["plus_hauts"]["code_iso"]) == ["DEU"]
    assert list(res["plus_bas"]["code_iso"]) == ["ESP"]


def test_top_plus_grand_que_le_nombre_de_pays():
    """
    Vérifie que si `top` dépasse le nombre de pays disponibles (10 > 3),
    aucune erreur n'est levée et `plus_hauts` comme `plus_bas` contiennent
    simplement tous les pays.
    """
    # GIVEN
    with patch.object(ObservationDAO, "lire", return_value=faux_df()):
        # WHEN
        res = ComparaisonPaysService().comparer_pays("X", classif1="15+", top=10)
    # THEN : pas d'erreur, on a simplement les 3 pays
    assert len(res["plus_hauts"]) == 3
    assert len(res["plus_bas"]) == 3


def test_deux_sources_pour_une_meme_periode():
    """
    Vérifie que, lorsqu'un pays a plusieurs sources pour la même période,
    une seule ligne est conservée : celle de la première source par ordre
    alphabétique ("A - Enquête"), ce qui rend le résultat déterministe.
    """
    # GIVEN : la France a deux sources pour 2024Q4
    df = pd.DataFrame({
        "code_iso": ["FRA", "FRA"],
        "nom_pays": ["France", "France"],
        "source": ["B - Enquête", "A - Enquête"],
        "periode": ["2024Q4", "2024Q4"],
        "valeur": [52.0, 51.0],
        "unite": ["%", "%"],
    })
    with patch.object(ObservationDAO, "lire", return_value=df):
        # WHEN
        res = ComparaisonPaysService().comparer_pays("X", classif1="15+")
    # THEN : une seule ligne, celle de la première source par ordre alphabétique ("A - ...")
    assert len(res["classement"]) == 1
    assert list(res["classement"]["valeur"]) == [51.0]


def test_dao_vide():
    """
    Vérifie que, lorsque le DAO ne renvoie aucune donnée, le service ne
    plante pas : la période de référence vaut None et le classement,
    `plus_hauts` et `plus_bas` sont des DataFrames vides.
    """
    # GIVEN : aucune donnée
    df_vide = pd.DataFrame(columns=["code_iso", "nom_pays", "source", "periode", "valeur", "unite"])
    with patch.object(ObservationDAO, "lire", return_value=df_vide):
        # WHEN
        res = ComparaisonPaysService().comparer_pays("X", classif1="15+")
    # THEN : pas d'erreur, résultat vide
    assert res["periode_reference"] is None
    assert res["classement"].empty
    assert res["plus_hauts"].empty
    assert res["plus_bas"].empty
