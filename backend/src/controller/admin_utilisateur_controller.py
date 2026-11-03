# Endpoints d'administration des comptes (préfixe /admin/utilisateurs, c.f. main.py)
# Tous réservés aux administrateurs : Depends(admin_requis) → 401 si pas connecté, 403 si pas admin.

from dataclasses import asdict

from business_object.utilisateur import Utilisateur
from config_import import INDICATEURS
from controller.auth import admin_requis
from fastapi import APIRouter, Depends, HTTPException, status
from fetcher.data_processing import DataProcessing
from schema.observation_model import CleObservationModel
from schema.utilisateur_model import CreationUtilisateurModel, UtilisateurModel
from service.journal_service import JournalService
from service.observation_service import ObservationService
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
def forcer_import(admin: Utilisateur = Depends(admin_requis)):  # noqa: B008
    nb_obs = DataProcessing().charger(INDICATEURS)

    if nb_obs is None:
        raise HTTPException(
            status_code=500,
            detail="Aucune observation n'a été enregistrée."
        )

    journal_ok = JournalService().enregistrer(action="import_donnees", utilisateur=admin)

    if not journal_ok:
        raise HTTPException(
            status_code=500,
            detail="Impossible d'enregistrer l'action dans le journal."
        )

    return {
        "message": "Import terminé.",
        "observations_enregistrees": nb_obs
    }


@router.put("observations")
def modifier_observation(
    cle: CleObservationModel,
    nouvelle_valeur: int,
    admin: Utilisateur = Depends(admin_requis)
):
    """
    Modifie une observation existante (identifiée par une cle) pour modifier sa valeur.
    Cette action est enregistré dans le journal
    """

    journal = JournalService().enregistrer(action="modification_donnee", utilisateur=admin, detail=f"modification de l'observation {cle}")

    if not journal:
        raise HTTPException(
            status_code=500,
            detail="Impossible d'enregistrer l'action dans le journal."
        )
    
    succes = ObservationService().modifier(
        cle, nouvelle_valeur
    )

    if not succes:
        raise HTTPException(
            status_code=404,
            detail="Observation introuvable."
        )

    return {"message": "Observation modifiée avec succès."}


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

@router.delete("/observation")
def supprimer_observation(
    cle: CleObservationModel,
    admin: Utilisateur = Depends(admin_requis),  # noqa: B008
):
    """
    Supprime une observation.
    Réservé aux administrateurs.
    """
    succes = ObservationService().supprimer(cle)

    journal = JournalService().enregistrer(action="suppression_donnee", utilisateur=admin)

    if not journal:
        raise HTTPException(
            status_code = 500,
            detail="Action non enregistré dans le journal"
        )

    if not succes:
        raise HTTPException(
            status_code=404,
            detail="Observation introuvable."
        )

    return {"message": "Observation supprimée avec succès."}
