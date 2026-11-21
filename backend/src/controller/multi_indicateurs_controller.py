"""Contrôleur API FastAPI pour l'analyse multi-indicateurs F5."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from business_object.selection import Selection
from controller.auth import utilisateur_connecte
from schema.multi_indicateurs_model import MultiIndicateursRequest, PointSerieModel
from service.multi_indicateurs_service import MultiIndicateursService

# routes réservées aux utilisateurs connectés (sinon 401), c.f. controller/auth.py
router = APIRouter(dependencies=[Depends(utilisateur_connecte)])
service = MultiIndicateursService()


@router.post(
    "/multi-indicateurs",
    response_model=list[PointSerieModel],
    summary="Comparer plusieurs indicateurs (F5)",
)
def comparer_indicateurs(requete: MultiIndicateursRequest) -> list[dict[str, Any]]:
    """Compare l'évolution temporelle de 1 à 4 indicateurs."""
    selections_bo = [
        Selection(indicateur=s.indicateur, pays=s.pays, classif1=s.classif1, sexe=s.sexe)
        for s in requete.selections
    ]

    try:
        df = service.comparer(selections_bo, base_100=requete.base_100)
    except ValueError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    df = df.astype(object).where(df.notna(), None)
    return df.to_dict(orient="records")
