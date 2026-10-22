
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from schema.evolution_model import EvolutionModel
from service.evolution_service import EvolutionService
from service.indicateur_service import IndicateurService

router = APIRouter()


@router.get("/evolution", response_model=list[EvolutionModel])
async def evolution_indicateur(
    indicateur: str = Query(description="Code de l'indicateur, ex : EMP_5WAP_SEX_AGE_RT_Q"),
    pays: list[str] = Query(description="Codes ISO"),
    classif1: str = Query(description="Profession ou tranche d'âge, ex : 15+"),
    sexe: Literal["Total", "Male", "Female"] = Query("Total", description="Total, Male ou Female"),
    n_periodes: int = Query(8, ge=1, le=40,
                            description="Nombre de dernières périodes (trimestres) par pays"),
):
    """
    Évolution d'un indicateur sur les N dernières périodes, pour chaque pays demandé :
    valeur, variation absolue et variation en % par rapport à la période précédente.
    Erreur si l'indicateur n'existe pas.
    """
    if IndicateurService().trouver_par_code(indicateur) is None:
        raise HTTPException(status_code=404, detail=f"Indicateur {indicateur} introuvable.")

    df = EvolutionService().evolution(indicateur, pays, classif1, sexe, n_periodes)

    # Le JSON n'accepte pas NaN: la première variation de chaque pays vaut None
    df = df.astype(object).where(df.notna(), None)

    # DataFrame :liste de dictionnaire (une par ligne) -> liste d'EvolutionModel
    # (format JSON de l'API)
    return [EvolutionModel(**ligne) for ligne in df.to_dict(orient="records")]
