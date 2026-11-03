"""Schémas Pydantic pour la fonctionnalité F5 (Comparaison Multi-Indicateurs)."""

from pydantic import BaseModel, ConfigDict, Field


class SelectionModel(BaseModel):
    """Filtres d'une courbe envoyés par le client (Streamlit / Client HTTP)."""

    model_config = ConfigDict(populate_by_name=True)

    indicateur: str = Field(
        ...,
        alias="code",
        description="Code de l'indicateur (ex: 'EMP_5EMP_SEX_OC2_NB_Q')",
    )
    pays: str = Field(..., description="Code ISO3 du pays (ex: 'FRA')")
    classif1: str = Field(..., description="Classification (ex: 'Total')")
    sexe: str = Field("Total", description="Filtre sexe")


class PointSerieModel(BaseModel):
    """Point de donnée renvoyé dans la réponse JSON de l'API."""

    serie: str = Field(..., description="Libellé complet de la série")
    indicateur: str = Field(..., description="Code de l'indicateur")
    periode: str = Field(..., description="Période (ex: '2024Q4')")
    valeur: float = Field(..., description="Valeur brute")
    unite: str = Field(..., description="Unité d'origine")
    valeur_base100: float = Field(..., description="Valeur calculée en base 100")