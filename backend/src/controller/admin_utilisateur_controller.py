# Endpoints d'administration des comptes (préfixe /admin/utilisateurs, c.f. main.py)
# Tous réservés aux administrateurs : Depends(admin_requis) → 401 si pas connecté, 403 si pas admin.

from dataclasses import asdict

from business_object.utilisateur import Utilisateur
from controller.auth import admin_requis
from fetcher.data_processing import DataProcessing
from fastapi import APIRouter, Depends, HTTPException, status
from schema.utilisateur_model import CreationUtilisateurModel, UtilisateurModel
from service.utilisateur_service import UtilisateurService

router = APIRouter()


@router.get("", response_model=list[UtilisateurModel])
def lister_utilisateurs(admin: Utilisateur = Depends(admin_requis)):
    """Liste tous les comptes (utilisateurs et administrateurs)."""
    return [UtilisateurModel(**asdict(u)) for u in UtilisateurService().lister()]


@router.post("", response_model=UtilisateurModel, status_code=status.HTTP_201_CREATED)
def creer_utilisateur(nouveau: CreationUtilisateurModel, admin: Utilisateur = Depends(admin_requis)):
    """
    Crée un compte, utilisateur ou administrateur.
    Erreur 400 si le pseudo ou le mot de passe est invalide, ou si le pseudo est déjà pris.
    """
    try:
        utilisateur = UtilisateurService().creer_compte(
            nouveau.pseudo, nouveau.mot_de_passe, nouveau.role, auteur=admin  # l'admin est noté au journal
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if utilisateur is None:
        raise HTTPException(status_code=400, detail="Ce pseudo est déjà utilisé.")
    return UtilisateurModel(**asdict(utilisateur))

@router.post("/import")
def forcer_import(admin: Utilisateur = Depends(admin_requis)):
    """
    Force le chargement de l'API externe
    """
    DataProcessing().charger(INDICATEURS)
    return


@router.delete("/{id_utilisateur}")
def supprimer_utilisateur(id_utilisateur: int, admin: Utilisateur = Depends(admin_requis)):
    """
    Supprime un compte à partir de son id (ses actions restent dans le journal).
    Erreur 400 si l'administrateur essaie de supprimer son propre compte, 404 si l'id n'existe pas.
    """
    try:
        supprime = UtilisateurService().supprimer(admin, id_utilisateur)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not supprime:
        raise HTTPException(status_code=404, detail=f"Utilisateur {id_utilisateur} introuvable.")
    return {"message": f"Utilisateur {id_utilisateur} supprimé."}
