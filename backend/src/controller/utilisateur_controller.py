# Endpoints de l'API concernant les comptes utilisateurs (préfixe /utilisateurs, c.f. main.py)

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status

from business_object.utilisateur import Utilisateur
from controller.auth import utilisateur_connecte
from schema.utilisateur_model import IdentifiantsModel, UtilisateurModel
from service.utilisateur_service import UtilisateurService

router = APIRouter()


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
    Crée un compte utilisateur (rôle 'utilisateur' : on ne peut pas se créer soi-même un compte admin).
    Erreur 400 si le pseudo ou le mot de passe est invalide, ou si le pseudo est déjà pris.
    """
    try:
        utilisateur = UtilisateurService().creer_compte(identifiants.pseudo, identifiants.mot_de_passe)
    except ValueError as e:  # règle non respectée (longueur du mot de passe...) : message pour l'utilisateur
        raise HTTPException(status_code=400, detail=str(e)) from e

    if utilisateur is None:
        raise HTTPException(status_code=400, detail="Ce pseudo est déjà utilisé.")
    return UtilisateurModel(**asdict(utilisateur))
