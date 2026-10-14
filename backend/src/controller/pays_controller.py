
from fastapi import APIRouter, Query
from schema.pays_model import PaysModel
from service.pays_service import PaysService

router = APIRouter()

@router.get("", response_model=list[PaysModel])  # "" : l'adresse est exactement /observations
async def lister_observations(
    code_iso: str = Query(description="code iso du pays ex: FRA pour la France"),
    nom_pays: str = Query(descrption="nom de pays, ex: France"),
    continent: str = Query(description="continent du pays, ex: Europe")
):
    """
    Liste tous les pays disponibles
    """

    return PaysService().lister()
