from fastapi import APIRouter, HTTPException, status
from schema.multi_indicateurs_model import PointSerieModel, SelectionModel

router = APIRouter()


@router.post(
    "/multi-indicateurs",
    response_model=list[PointSerieModel],
    status_code=status.HTTP_200_OK,
    summary="Comparer plusieurs indicateurs en base 100 (F5)",
)
async def comparer_indicateurs(selections: list[SelectionModel]):
    """Compare l'évolution de 2 à 4 indicateurs ramenés sur une base 100."""
    if len(selections) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Au moins 2 sélections sont requises pour effectuer une comparaison.",
        )

    # Note : La logique du service MultiIndicateursService sera branchée à l'Étape 2.
    return []