"""Contrôleur API FastAPI pour l'analyse multi-indicateurs F5."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from business_object.selection import Selection
from schema.multi_indicateurs_model import PointSerieModel, MultiIndicateursRequest
from service.multi_indicateurs_service import MultiIndicateursService

router = APIRouter()
service = MultiIndicateursService()


@router.post(
    "/multi-indicateurs",
    response_model=list[PointSerieModel],
    summary="Comparer plusieurs indicateurs (F5)",
)
async def comparer_indicateurs(requete: MultiIndicateursRequest) -> list[dict[str, Any]]:
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
