"""Schémas Pydantic pour la fonctionnalité F5 (Comparaison Multi-Indicateurs)."""

from pydantic import BaseModel, Field


class SelectionModel(BaseModel):
    """Une série à comparer (indicateur, pays, filtres)."""

    indicateur: str = Field(..., alias="code_indicateur")
    pays: str = Field(..., alias="code_iso")
    classif1: str | None = None
    sexe: str = "Total"

    model_config = {"populate_by_name": True}


class MultiIndicateursRequest(BaseModel):
    """Requête de comparaison : 1 à 4 séries."""

    selections: list[SelectionModel] = Field(..., min_length=1, max_length=4)
    base_100: bool = True
