# Endpoints de l'API concernant les observations (préfixe /observations, c.f. main.py)

from fastapi import APIRouter, HTTPException, Query

from schema.observation_model import ObservationModel
from service.indicateur_service import IndicateurService
from service.observation_service import ObservationService

router = APIRouter()


@router.get("", response_model=list[ObservationModel])  # "" : l'adresse est exactement /observations
async def lister_observations(
    indicateur: str = Query(description="Code de l'indicateur, ex : EMP_5WAP_SEX_AGE_RT_Q"),
    pays: list[str] | None = Query(None, description="Codes ISO, ex : FRA (répéter pour plusieurs pays)"),
    periode_min: str | None = Query(None, description="Première période incluse, ex : 2024Q1"),
    periode_max: str | None = Query(None, description="Dernière période incluse, ex : 2024Q4"),
    sexe: str | None = Query(None, description="Total, Male ou Female"),
    classif1: str | None = Query(None, description="Profession ou tranche d'âge, ex : 15-24"),
    limite: int = Query(100, ge=1, le=10000, description="Nombre maximum d'observations renvoyées"),
):
    """
    Liste les observations d'un indicateur, avec des filtres facultatifs.
    Erreur 404 si l'indicateur n'existe pas.
    """
    if IndicateurService().trouver_par_code(indicateur) is None:
        raise HTTPException(status_code=404, detail=f"Indicateur {indicateur} introuvable.")

    df = ObservationService().lister(indicateur, pays, periode_min, periode_max, sexe, classif1, limite)

    # DataFrame -> liste de dict (une par ligne) -> liste d'ObservationModel (format JSON de l'API)
    return [ObservationModel(**ligne) for ligne in df.to_dict(orient="records")]
