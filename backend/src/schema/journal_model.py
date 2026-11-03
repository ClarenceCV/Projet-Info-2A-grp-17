# Format JSON du journal des actions renvoyé par l'API (GET /admin/journal).

from datetime import datetime

from pydantic import BaseModel


class ActionJournalModel(BaseModel):
    """
    Une action du journal.
    ex : {"id": 12, "date": "2026-11-03T10:15:00", "pseudo": "admin", "action": "connexion",
          "libelle_action": "Connexion", "detail": null, "utilisateur_id": 2}
    """

    id: int
    date: datetime
    pseudo: str | None = None
    action: str
    libelle_action: str          # libellé lisible de l'action, ex : 'Échec de connexion'
    detail: str | None = None
    utilisateur_id: int | None = None  # None si le compte a été supprimé depuis
