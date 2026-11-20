"""Endpoints de l'API concernant les comptes utilisateurs (préfixe /utilisateurs, c.f. main.py)"""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status

from business_object.utilisateur import Utilisateur
from controller.auth import utilisateur_connecte
from schema.utilisateur_model import IdentifiantsModel, UtilisateurModel
from service.utilisateur_service import UtilisateurService

router = APIRouter()


def creer_compte_ou_erreur_400(*args, **kwargs) -> UtilisateurModel:
    """
    Crée un compte et le renvoie au format de l'API.
    Utilisée aussi par admin_utilisateur_controller (création d'un compte par un admin).

    Args:
        *args, **kwargs: transmis tels quels à UtilisateurService.creer_compte
            (pseudo, mot_de_passe, et pour un admin : role, auteur)

    Raises:
        HTTPException 400: pseudo ou mot de passe invalide, ou pseudo déjà pris
    """
    try:
        utilisateur = UtilisateurService().creer_compte(*args, **kwargs)
    # règle non respectée (longueur du mot de passe...) : message pour l'utilisateur
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if utilisateur is None:
        raise HTTPException(status_code=400, detail="Ce pseudo est déjà utilisé.")
    return UtilisateurModel(**asdict(utilisateur))


@router.get("/moi", response_model=UtilisateurModel)
def qui_suis_je(utilisateur: Utilisateur = Depends(utilisateur_connecte)):
    """
    Renvoie l'utilisateur connecté (celui à qui appartient le token).
    Erreur 401 si personne n'est connecté.
    """
    return UtilisateurModel(**asdict(utilisateur))


# def (et pas async def) : bcrypt met ~0,4 s à hacher et psycopg2 attend la base ;
# FastAPI exécute alors la fonction à part, sans bloquer les autres requêtes pendant ce temps.
@router.post("", response_model=UtilisateurModel, status_code=status.HTTP_201_CREATED)
def creer_compte(identifiants: IdentifiantsModel):
    """
    Crée un compte utilisateur (rôle 'utilisateur' : on ne peut pas se créer soi-même un compte
    admin).
    Erreur 400 si le pseudo ou le mot de passe est invalide, ou si le pseudo est déjà pris.
    """
    return creer_compte_ou_erreur_400(identifiants.pseudo, identifiants.mot_de_passe)
