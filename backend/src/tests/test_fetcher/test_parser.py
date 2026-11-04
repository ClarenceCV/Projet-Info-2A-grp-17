import pandas as pd
import pytest

from fetcher.parser import retirer_prefixe


# ============================================================
# TESTS DE RETIRER_PREFIXE
# ============================================================

def test_retirer_prefixe_simple():
    """Vérifie le retrait d'un préfixe simple."""

    resultat = retirer_prefixe("Sex: Female")

    assert resultat == "Female"


def test_retirer_prefixe_age():
    """Vérifie le retrait d'un préfixe contenant des parenthèses."""

    resultat = retirer_prefixe("Age (Youth, adults): 15-64")

    assert resultat == "15-64"


def test_retirer_prefixe_sans_prefixe():
    """Vérifie le comportement lorsqu'il n'y a pas de préfixe."""

    resultat = retirer_prefixe("France")

    assert resultat == "France"


def test_retirer_prefixe_plusieurs_deux_points():
    """Vérifie que seul le premier préfixe est retiré."""

    resultat = retirer_prefixe("Classification: Type: A")

    assert resultat == "Type: A"


def test_retirer_prefixe_espaces():
    """Vérifie la suppression des espaces autour du libellé."""

    resultat = retirer_prefixe("  Sex: Female  ")

    assert resultat == "Female"


def test_retirer_prefixe_none():
    """Vérifie le comportement avec une valeur None."""

    resultat = retirer_prefixe(None)

    assert resultat is None


def test_retirer_prefixe_nan():
    """Vérifie le comportement avec une valeur NaN."""

    resultat = retirer_prefixe(float("nan"))

    assert resultat is None


def test_retirer_prefixe_pandas_na():
    """Vérifie le comportement avec une valeur pd.NA."""

    resultat = retirer_prefixe(pd.NA)

    assert resultat is None


def test_retirer_prefixe_chaine_vide():
    """Vérifie le comportement avec une chaîne vide."""

    resultat = retirer_prefixe("")

    assert resultat == ""


def test_retirer_prefixe_prefixe_sans_espace():
    """Vérifie le comportement lorsqu'il n'y a pas d'espace après les deux-points."""

    resultat = retirer_prefixe("Sex:Female")

    assert resultat == "Sex:Female"
