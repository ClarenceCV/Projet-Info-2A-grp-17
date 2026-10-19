# Endpoints de l'API concernant les indicateurs (préfixe /indicateurs, c.f. main.py)

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from schema.indicateur_model import IndicateurModel, IndicateurClassif1Model

from service.indicateur_service import IndicateurService
from service.observation_service import ObservationService

router = APIRouter()


@router.get("", response_model=list[IndicateurModel])  # "" : l'adresse est exactement /indicateurs
async def lister_indicateurs():
    """Liste les indicateurs disponibles dans la base."""
    indicateurs = IndicateurService().lister()
    # objet Indicateur (dataclass) -> dict -> IndicateurModel (format JSON de l'API)
    return [IndicateurModel(**asdict(indicateur)) for indicateur in indicateurs]


@router.get("/{code}", response_model=IndicateurModel)
async def indicateur_par_code(code: str):
    """
    Renvoie un indicateur à partir de son code (ex : EMP_5EMP_SEX_OC2_NB_Q).
    Erreur 404 si l'indicateur n'existe pas.
    """
    indicateur = IndicateurService().trouver_par_code(code)
    if indicateur is None:
        raise HTTPException(status_code=404, detail=f"Indicateur {code} introuvable.")
    return IndicateurModel(**asdict(indicateur))


@router.get("/{code}/classif1", response_model=IndicateurClassif1Model)
async def liste_classif1(code: str):
    indicateur = IndicateurService().trouver_par_code(code)
    if indicateur is None:
        raise HTTPException(status_code=404, detail=f"Indicateur {code} introuvable.")
    modalites = ObservationService().lister_classif1(code)
    return IndicateurClassif1Model(code=code, modalites=modalites)
