from dataclasses import dataclass
from datetime import datetime

# Actions enregistrées dans le journal (mot-clé court, filtrable).
# Pour une nouvelle action : l'ajouter ici, puis appeler JournalService().enregistrer(...)
ACTIONS = {
    "connexion": "Connexion",
    "echec_connexion": "Échec de connexion",
    "deconnexion": "Déconnexion",
    "creation_compte": "Création de compte",
    "suppression_compte": "Suppression de compte",
    # actions sur les données (responsable A) :
    "import_donnees": "Import des données ILOSTAT",
    "modification_donnee": "Modification d'une donnée",
    "suppression_donnee": "Suppression d'une donnée",
}


@dataclass
class ActionJournal:
    """
    Une action enregistrée dans le journal (une ligne de la table journal).

    Attributes:
        action (str): mot-clé de l'action, une des clés de ACTIONS, ex : 'connexion'
        pseudo (str | None): qui a fait l'action (copié au moment de l'action)
        detail (str | None): précision libre, ex : 'rôle admin'
        utilisateur_id (int | None): id du compte, None si le compte a été supprimé depuis
        id (int | None): identifiant en base
        date (datetime | None): date de l'action (remplie par la base)
    """

    action: str
    pseudo: str | None = None
    detail: str | None = None
    utilisateur_id: int | None = None
    id: int | None = None
    date: datetime | None = None

    def __post_init__(self):
        """Vérifie que l'action fait partie de la liste connue"""
        if self.action not in ACTIONS:
            raise ValueError(f"action should be one of {list(ACTIONS)}")
