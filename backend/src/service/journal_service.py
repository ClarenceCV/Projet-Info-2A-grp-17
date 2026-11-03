# Journal des actions (F6 : « suivi des activités » par l'administrateur).
#
# Utilisation par les autres services (ex : A pour les actions sur les données) :
#     from service.journal_service import JournalService
#     JournalService().enregistrer(utilisateur, "suppression_donnee", "FRA, 2024Q4, Female, 15-24")
# (l'action doit faire partie de ACTIONS, c.f. business_object/action_journal.py)

from business_object.action_journal import ActionJournal
from business_object.utilisateur import Utilisateur
from dao.journal_dao import JournalDAO


class JournalService:
    """
    Service du journal des actions.
    """

    def enregistrer(
        self,
        utilisateur: Utilisateur | None,
        action: str,
        detail: str | None = None,
        pseudo: str | None = None,
    ) -> bool:
        """
        Enregistre une action dans le journal.
        Ne fait JAMAIS échouer l'action principale : si l'écriture dans le journal échoue,
        un avertissement est affiché et l'application continue.

        params:
            utilisateur: qui fait l'action (None si inconnu, ex : échec de connexion)
            action: mot-clé, ex : 'connexion' (c.f. ACTIONS)
            detail: précision libre
            pseudo: pseudo à noter quand il n'y a pas d'utilisateur (ex : pseudo essayé)

        Returns:
            bool: True si l'action a été enregistrée
        """
        try:
            entree = ActionJournal(
                action=action,
                pseudo=utilisateur.pseudo if utilisateur else pseudo,
                detail=detail,
                utilisateur_id=utilisateur.id if utilisateur else None,
            )
            return JournalDAO().enregistrer(entree)
        except Exception as e:  # journal indisponible : on le signale, sans bloquer l'utilisateur
            print(f"Attention : action '{action}' non enregistrée dans le journal ({e})")
            return False

    def lister(
        self, action: str | None = None, pseudo: str | None = None, limite: int = 200
    ) -> list[ActionJournal]:
        """
        Returns:
            list[ActionJournal]: les actions, les plus récentes d'abord (c.f. JournalDAO.lister)
        """
        return JournalDAO().lister(action, pseudo, limite)
