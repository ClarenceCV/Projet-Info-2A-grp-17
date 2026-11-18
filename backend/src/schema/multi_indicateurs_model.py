"""Schémas Pydantic pour la fonctionnalité F5 (Comparaison Multi-Indicateurs)."""

from pydantic import BaseModel, Field


class SelectionModel(BaseModel):
    code_indicateur: str
    code_iso: str
    classif1: str | None = None
    sexe: str = "Total"


class PointSerieModel(BaseModel):
    """Point de donnée renvoyé dans la réponse JSON de l'API."""

    serie: str = Field(..., description="Libellé complet de la série")
    indicateur: str = Field(..., description="Code de l'indicateur")
    periode: str = Field(..., description="Période (ex: '2024Q4')")
    valeur: float = Field(..., description="Valeur brute")
    unite: str = Field(..., description="Unité d'origine")
    valeur_base100: float | None = None


class MultiIndicateursRequest(BaseModel):
    selections: list[SelectionModel]
    base_100: bool = True
