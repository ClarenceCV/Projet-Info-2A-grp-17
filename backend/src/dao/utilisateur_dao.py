# Accès à la table utilisateur. Entrée : valeurs Python ; sortie : objets Utilisateur
# (inspiré du PlayerDao du template ENSAI : create, find_by_token, update, delete)

from psycopg2.errors import UniqueViolation

from business_object.utilisateur import Utilisateur
from dao.db_connection import DBConnection

# Colonnes lues pour construire un Utilisateur (jamais le hash du mot de passe)
COLONNES_UTILISATEUR = "id, pseudo, role, date_creation"


class UtilisateurDAO:
    """
    Accès aux utilisateurs dans la base de données.
    """

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def creer(self, pseudo: str, mdp_hash: str, role: str = "utilisateur") -> Utilisateur | None:
        """
        Enregistre un nouvel utilisateur.

        params:
            pseudo: identifiant de connexion
            mdp_hash: hash bcrypt du mot de passe (calculé par le service, jamais le mot de passe)
            role: 'utilisateur' ou 'admin'

        Returns:
            Utilisateur | None: l'utilisateur créé (avec son id), ou None si le pseudo est déjà pris
        """
        try:
            with DBConnection().connection as connection:  # noqa: SIM117
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO laborscope.utilisateur (pseudo, mdp_hash, role) "
                        "VALUES (%(pseudo)s, %(mdp_hash)s, %(role)s) "
                        f"RETURNING {COLONNES_UTILISATEUR};",
                        {"pseudo": pseudo, "mdp_hash": mdp_hash, "role": role},
                    )
                    ligne = cursor.fetchone()
        except UniqueViolation:
            # contrainte UNIQUE sur pseudo : la base refuse le doublon (et annule la transaction)
            return None

        return Utilisateur(**ligne)

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    def trouver_par_pseudo(self, pseudo: str) -> Utilisateur | None:
        """
        Returns:
            Utilisateur | None: l'utilisateur, ou None s'il n'existe pas
        """
        return self._trouver("pseudo", pseudo)

    def trouver_par_token(self, token: str | None) -> Utilisateur | None:
        """
        Retrouve l'utilisateur connecté à partir de son token (utilisé à chaque requête protégée).

        Returns:
            Utilisateur | None: l'utilisateur, ou None si le token est absent ou inconnu
        """
        if not token:
            return None
        return self._trouver("token", token)

    def lire_mdp_hash(self, pseudo: str) -> str | None:
        """
        Lit le hash du mot de passe d'un utilisateur (seulement pour vérifier une connexion).

        Returns:
            str | None: le hash bcrypt, ou None si le pseudo n'existe pas
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT mdp_hash FROM laborscope.utilisateur WHERE pseudo = %(pseudo)s;",
                    {"pseudo": pseudo},
                )
                ligne = cursor.fetchone()
        return ligne["mdp_hash"] if ligne else None

    def lister(self) -> list[Utilisateur]:
        """
        Returns:
            list[Utilisateur]: tous les utilisateurs, triés par pseudo
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {COLONNES_UTILISATEUR} FROM laborscope.utilisateur ORDER BY pseudo;"
                )
                lignes = cursor.fetchall()
        return [Utilisateur(**ligne) for ligne in lignes]

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def enregistrer_token(self, id_utilisateur: int, token: str | None) -> bool:
        """
        Enregistre le token de session d'un utilisateur (connexion),
        ou l'efface avec token=None (déconnexion).

        Returns:
            bool: True si l'utilisateur existe (une ligne modifiée)
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE laborscope.utilisateur SET token = %(token)s WHERE id = %(id)s;",
                    {"token": token, "id": id_utilisateur},
                )
                return cursor.rowcount == 1

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def supprimer(self, id_utilisateur: int) -> bool:
        """
        Supprime un utilisateur. Ses lignes de journal sont gardées (utilisateur_id passe à NULL).

        Returns:
            bool: True si un utilisateur a été supprimé, False si l'id n'existe pas
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM laborscope.utilisateur WHERE id = %(id)s;",
                    {"id": id_utilisateur},
                )
                return cursor.rowcount == 1

    # ------------------------------------------------------------------
    # Méthode commune aux recherches d'un seul utilisateur
    # ------------------------------------------------------------------
    def _trouver(self, colonne: str, valeur: str) -> Utilisateur | None:
        """
        Cherche un utilisateur par la valeur d'une colonne ('pseudo' ou 'token').
        Le nom de colonne vient uniquement de ce fichier (jamais de l'utilisateur) :
        pas de risque d'injection SQL.
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {COLONNES_UTILISATEUR} FROM laborscope.utilisateur "
                    f"WHERE {colonne} = %(valeur)s;",
                    {"valeur": valeur},
                )
                ligne = cursor.fetchone()
        return Utilisateur(**ligne) if ligne else None
