
from pydantic import BaseModel


class EvolutionModel(BaseModel):
    """
    Un point de l'évolution d'un indicateur : un pays, une période.
    ex : {"code_iso": "FRA", "nom_pays": "France", "periode": "2024Q4", "valeur": 52.07,
          "unite": "%", "variation_abs": 0.31, "variation_pct": 0.6}
    variation_abs et variation_pct valent null pour la première période (pas de précédente).
    """

    code_iso: str
    nom_pays: str
    periode: str
    valeur: float
    unite: str
    variation_abs: float | None = None
    variation_pct: float | None = None
