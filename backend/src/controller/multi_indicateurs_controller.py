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
    status_code=status.HTTP_200_OK,
    summary="Comparer plusieurs indicateurs (F5)",
)
async def comparer_indicateurs(
    requete: MultiIndicateursRequest,
) -> list[dict[str, Any]]:
    """Compare l'évolution temporelle de 1 à 4 indicateurs."""
    if len(requete.selections) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Au moins 1 sélection est requise.",
        )

    selections_bo = [
        Selection(
            indicateur=s.code_indicateur,
            pays=s.code_iso,
            classif1=s.classif1,
            sexe=s.sexe,
        )
        for s in requete.selections
    ]

    try:
        df_resultat = service.comparer(selections_bo, base_100=requete.base_100)

        if df_resultat.empty:
            return []

        df_resultat = df_resultat.fillna("")
        return df_resultat.to_dict(orient="records")

    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err