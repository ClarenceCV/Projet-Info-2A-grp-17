"""
Format JSON des pays échangé entre le backend et ses clients (navigateur, frontend).
Permet de faire le lien avec Evolution et avec la comparaison des pays (F3) et (F4).
"""

from pydantic import BaseModel


class PaysModel(BaseModel):
    """Pays de base."""

    code_iso: str
    nom_pays: str


class PaysValeurModel(PaysModel):
    """Valeur d'un indicateur pour un pays à une période."""

    periode: str
    valeur: float
    unite: str


class PaysClasseModel(PaysValeurModel):
    """Un pays du classement.
    ex : {"rang": 1, "code_iso": "DEU", "nom_pays": "Germany", "periode": "2024Q4",
          "valeur": 61.2, "unite": "%"}
    """

    rang: int


class EvolutionModel(PaysValeurModel):
    """Un point de l'évolution d'un indicateur : un pays, une période.
    variation_abs et variation_pct valent null pour la première période.
    ex : {"code_iso": "FRA", "nom_pays": "France", "periode": "2024Q4", "valeur": 52.07,
          "unite": "%", "variation_abs": 0.31, "variation_pct": 0.6}
    Utile pour F4
    """

    variation_abs: float | None = None
    variation_pct: float | None = None
