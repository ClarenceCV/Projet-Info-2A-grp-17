# Endpoint du journal des actions (préfixe /admin/journal, c.f. main.py) : réservé aux administrateurs.

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from business_object.action_journal import ACTIONS
from business_object.utilisateur import Utilisateur
from controller.auth import admin_requis
from schema.journal_model import ActionJournalModel
from service.journal_service import JournalService

router = APIRouter()


@router.get("", response_model=list[ActionJournalModel])
def lire_journal(
    action: str | None = Query(None, description=f"Une seule action : {', '.join(ACTIONS)}"),
    pseudo: str | None = Query(None, description="Début du pseudo, ex : ad pour admin"),
    limite: int = Query(200, ge=1, le=5000, description="Nombre maximum d'actions renvoyées"),
    admin: Utilisateur = Depends(admin_requis),
):
    """
    Historique des actions des utilisateurs (connexions, créations, suppressions...), les plus récentes d'abord.
    """
    actions = JournalService().lister(action, pseudo, limite)
    return [ActionJournalModel(**asdict(a), libelle_action=ACTIONS[a.action]) for a in actions]
