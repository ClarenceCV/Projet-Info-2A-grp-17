from dataclasses import dataclass


@dataclass(frozen=True)
class Selection:
    """Un indicateur plus ses filtres : une courbe du graphique multi-indicateurs (F5)."""

    indicateur: str
    pays: str
    classif1: str
    sexe: str = "Total"

