# Accès à la table journal. Entrée : objet ActionJournal ; sortie : objets ActionJournal

from dataclasses import asdict

from business_object.action_journal import ActionJournal
from dao.db_connection import DBConnection

COLONNES_JOURNAL = "id, utilisateur_id, pseudo, action, detail, date"


class JournalDAO:
    """
    Accès au journal des actions dans la base de données.
    """

    def enregistrer(self, action: ActionJournal) -> bool:
        """
        Ajoute une action au journal (la date est remplie par la base).

        Returns:
            bool: True si l'action a été enregistrée
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO laborscope.journal (utilisateur_id, pseudo, action, detail) "
                    "VALUES (%(utilisateur_id)s, %(pseudo)s, %(action)s, %(detail)s);",
                    asdict(action),  # les clés en trop (id, date) sont ignorées par psycopg2
                )
                return cursor.rowcount == 1

    def lister(
        self, action: str | None = None, pseudo: str | None = None, limite: int = 200
    ) -> list[ActionJournal]:
        """
        Lit les actions du journal, les plus récentes d'abord. Chaque filtre laissé à None est ignoré.

        params:
            action: mot-clé exact, ex : 'connexion'
            pseudo: début du pseudo, sans tenir compte des majuscules, ex : 'ad' trouve 'admin'
            limite: nombre maximum d'actions renvoyées

        Returns:
            list[ActionJournal]
        """
        conditions = []
        if action is not None:
            conditions.append("action = %(action)s")
        if pseudo:
            conditions.append("pseudo ILIKE %(pseudo)s")  # ILIKE : LIKE sans tenir compte de la casse
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {COLONNES_JOURNAL} FROM laborscope.journal {where} "
                    "ORDER BY date DESC, id DESC LIMIT %(limite)s;",
                    {"action": action, "pseudo": f"{pseudo}%", "limite": limite},
                )
                lignes = cursor.fetchall()
        return [ActionJournal(**ligne) for ligne in lignes]
