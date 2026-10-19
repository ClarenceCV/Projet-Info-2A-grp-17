
from fastapi import APIRouter, Query
from schema.pays_model import PaysModel
from service.pays_service import PaysService

router = APIRouter()

@router.get("", response_model=list[PaysModel])  # "" : l'adresse est exactement /observations
async def lister_observations():
    """
    Liste tous les pays disponibles
    """
    return PaysService().lister()
