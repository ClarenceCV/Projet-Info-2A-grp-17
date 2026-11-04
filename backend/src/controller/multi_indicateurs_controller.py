"""Contrôleur API FastAPI pour l'analyse multi-indicateurs F5."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from business_object.selection import Selection
from schema.multi_indicateurs_model import PointSerieModel, SelectionModel
from service.multi_indicateurs_service import MultiIndicateursService

router = APIRouter()
service = MultiIndicateursService()


@router.post(
    "/multi-indicateurs",
    response_model=list[PointSerieModel],
    status_code=status.HTTP_200_OK,
    summary="Comparer plusieurs indicateurs en base 100 (F5)",
)
async def comparer_indicateurs(
    selections: list[SelectionModel],
) -> list[dict[str, Any]]:
    """Compare l'évolution temporelle de 2 à 4 indicateurs ramenés en base 100."""
    if len(selections) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Au moins 2 sélections sont requises pour effectuer une comparaison.",
        )

    # Instanciation explicite des dataclasses Selection
    selections_bo = [
        Selection(
            indicateur=s.indicateur,
            pays=s.pays,
            classif1=s.classif1,
            sexe=s.sexe,
        )
        for s in selections
    ]

    try:
        df_resultat = service.comparer(selections_bo)

        if df_resultat.empty:
            return []

        # Remplacement des valeurs manquantes/NaN pour éviter les erreurs de sérialisation JSON
        df_resultat = df_resultat.fillna("")
        return df_resultat.to_dict(orient="records")

    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err