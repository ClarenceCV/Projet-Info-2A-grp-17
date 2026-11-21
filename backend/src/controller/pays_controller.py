"""Endpoint de la liste des pays disponibles, préfixe /pays (c.f. main.py)."""

from fastapi import APIRouter, Depends

from controller.auth import utilisateur_connecte
from schema.pays_model import PaysModel
from service.pays_service import PaysService

# routes réservées aux utilisateurs connectés (sinon 401), c.f. controller/auth.py
router = APIRouter(dependencies=[Depends(utilisateur_connecte)])


@router.get("", response_model=list[PaysModel])  # "" : l'adresse est exactement /pays
def lister_pays():
    """Liste tous les pays disponibles (code ISO et nom)."""
    return PaysService().lister()
