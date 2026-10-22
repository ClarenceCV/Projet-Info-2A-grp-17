from pydantic import BaseModel, Field


class SelectionModel(BaseModel):
    """Représente une sélection d'un indicateur avec ses filtres (ce que le client envoie)."""

    indicateur: str = Field(
        ...,
        description="Code de l'indicateur (ex: 'EMP_5EMP_SEX_OC2_NB_Q')",
        examples=["EMP_5EMP_SEX_OC2_NB_Q"],
    )
    pays: str = Field(
        ..., description="Code ISO3 du pays (ex: 'FRA')", examples=["FRA"]
    )
    classif1: str = Field(
        ...,
        description="Classification (ex: 'Total' ou '15+')",
        examples=["Total"],
    )
    sexe: str = Field(
        "Total", description="Filtre sur le sexe", examples=["Total"]
    )


class PointSerieModel(BaseModel):
    """Représente un point d'une série temporelle en base 100 (ce que l'API renvoie)."""

    serie: str = Field(
        ...,
        description="Nom complet lisible de la série (ex: 'Emploi — France — Total — Total')",
    )
    indicateur: str = Field(..., description="Code de l'indicateur")
    periode: str = Field(..., description="Période (ex: '2024Q4')")
    valeur: float = Field(..., description="Valeur brute de l'observation")
    unite: str = Field(..., description="Unité de mesure d'origine")
    valeur_base100: float = Field(
        ..., description="Valeur ramenée en base 100"
    )