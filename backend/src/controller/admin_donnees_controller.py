"""Endpoints d'administration des données (préfixe /admin, c.f. main.py) :
import ILOSTAT, modification et suppression d'observations, lecture des logs techniques.
Tous réservés aux administrateurs : Depends(admin_requis) → 401 si pas connecté, 403 si pas admin.
Chaque action réussie est notée au journal (le journal ne fait jamais échouer l'action, c.f.
JournalService).
"""

from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query

from business_object.utilisateur import Utilisateur
from config_import import INDICATEURS
from controller.auth import admin_requis
from fetcher.data_processing import DataProcessing
from schema.observation_model import CleObservationModel
from service.journal_service import JournalService
from service.observation_service import ObservationService
from utils.log_utils import LOG_DIR

router = APIRouter()


def decrire(cle: CleObservationModel) -> str:
    """Résumé lisible d'une observation pour le journal, ex : 'EMP_5WAP_SEX_AGE_RT_Q, FRA, 2024Q4,
    ...'."""
    return ", ".join(str(valeur) for valeur in cle.model_dump().values())


@router.post("/import")
def forcer_import(admin: Utilisateur = Depends(admin_requis)):
    """
    Relance l'import ILOSTAT de tous les indicateurs suivis (c.f. config_import.py).
    Peut prendre plusieurs minutes. Les observations déjà présentes sont mises à jour, pas
    dupliquées.
    """
    nb_obs = DataProcessing().charger(INDICATEURS)
    JournalService().enregistrer(admin, "import_donnees", f"{nb_obs} observations enregistrées")
    return {"message": "Import terminé.", "observations_enregistrees": nb_obs}


@router.put("/observations")
def modifier_observation(
    cle: CleObservationModel,
    nouvelle_valeur: float,
    admin: Utilisateur = Depends(admin_requis),
):
    """
    Modifie la valeur d'une observation, identifiée par sa clé (corps de la requête).
    Erreur 404 si l'observation n'existe pas.
    """
    if not ObservationService().modifier(cle, nouvelle_valeur):
        raise HTTPException(status_code=404, detail="Observation introuvable.")

    JournalService().enregistrer(
        admin, "modification_donnee", f"{decrire(cle)} → {nouvelle_valeur}"
    )
    return {"message": "Observation modifiée avec succès."}


@router.delete("/observations")
def supprimer_observation(cle: CleObservationModel, admin: Utilisateur = Depends(admin_requis)):
    """
    Supprime une observation, identifiée par sa clé (corps de la requête).
    Erreur 404 si l'observation n'existe pas.
    """
    if not ObservationService().supprimer(cle):
        raise HTTPException(status_code=404, detail="Observation introuvable.")

    JournalService().enregistrer(admin, "suppression_donnee", decrire(cle))
    return {"message": "Observation supprimée avec succès."}


# dependencies=[...] : la garde est exécutée, mais la route n'a pas besoin de l'admin lui-même
@router.get("/logs", dependencies=[Depends(admin_requis)])
def lire_logs(
    lignes: int = Query(default=100, ge=1, le=5000, description="Nombre de lignes à renvoyer"),
):
    """Renvoie les dernières lignes du fichier de logs techniques du backend."""
    fichier_log = LOG_DIR / "laborscope.log"
    if not fichier_log.exists():
        raise HTTPException(status_code=404, detail="Fichier de logs introuvable.")

    with fichier_log.open("r", encoding="utf-8") as fichier:
        # deque : garde seulement les n dernières
        dernieres_lignes = list(deque(fichier, maxlen=lignes))

    return {"nombre_lignes": len(dernieres_lignes), "logs": dernieres_lignes}
