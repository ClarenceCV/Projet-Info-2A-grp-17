# Endpoint de la comparaison entre pays (F4) (préfixe /analyses, c.f. main.py)

from fastapi import APIRouter, HTTPException, Query

from schema.comparaison_pays_model import ComparaisonPaysModel
from service.comparaison_pays_service import ComparaisonPaysService
from service.indicateur_service import IndicateurService

router = APIRouter()


@router.get("/comparaison-pays", response_model=ComparaisonPaysModel)
async def comparer_pays(
    indicateur: str = Query(description="Code de l'indicateur, ex : EMP_5WAP_SEX_AGE_RT_Q"),
    classif1: str = Query(description="Profession ou tranche d'âge, ex : 15+"),
    pays: list[str] | None = Query(None, description="Codes ISO, ex : FRA (répéter pour plusieurs pays ; vide = tous)"),
    sexe: str = Query("Total", description="Total, Male ou Female"),
    top: int = Query(3, ge=1, le=50, description="Nombre de pays dans plus_hauts et plus_bas"),
):
    """
    Compare un indicateur entre pays, à la dernière période disponible de chaque pays :
    classement par valeur décroissante, pays les plus hauts et les plus bas.
    Erreur 404 si l'indicateur n'existe pas.
    """
    if IndicateurService().trouver_par_code(indicateur) is None:
        raise HTTPException(status_code=404, detail=f"Indicateur {indicateur} introuvable.")

    resultat = ComparaisonPaysService().comparer_pays(indicateur, classif1, pays, sexe, top)

    # chaque DataFrame -> liste de dict (une par ligne) -> format JSON de l'API
    return ComparaisonPaysModel(
        periode_reference=resultat["periode_reference"],
        classement=resultat["classement"].to_dict(orient="records"),
        plus_hauts=resultat["plus_hauts"].to_dict(orient="records"),
        plus_bas=resultat["plus_bas"].to_dict(orient="records"),
    )
