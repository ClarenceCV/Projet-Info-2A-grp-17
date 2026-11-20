"""Endpoint de la liste des pays disponibles, préfixe /pays (c.f. main.py)."""

from fastapi import APIRouter

from schema.pays_model import PaysModel
from service.pays_service import PaysService

router = APIRouter()

@router.get("", response_model=list[PaysModel])  # "" : l'adresse est exactement /observations
async def lister_observations():
    """
    Liste tous les pays disponibles
    """
    return PaysService().lister()
