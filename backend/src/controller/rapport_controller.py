"""Contrôleur FastAPI pour l'exportation du rapport PDF (FO3)."""

from fastapi import APIRouter, Query, Response, status

from service.rapport_service import RapportService

router = APIRouter(tags=["Rapport"])


@router.get(
    "/rapport",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Générer et télécharger un rapport PDF d'analyse",
)
def generer_rapport(
    indicateur: str = Query(..., description="Code de l'indicateur"),
    pays: list[str] = Query(..., description="Liste des codes ISO pays"),
    classif1: str = Query("Total", description="Classification"),
    sexe: str = Query("Total", description="Filtre sexe"),
    n_periodes: int = Query(8, ge=2, le=40, description="Nombre de périodes"),
) -> Response:
    """Génère à la volée un rapport au format PDF."""
    pdf_bytes = RapportService().generer(
        code_indicateur=indicateur,
        pays=pays,
        classif1=classif1,
        sexe=sexe,
        n_periodes=n_periodes,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=rapport_laborscope.pdf"},
    )