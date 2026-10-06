# Accès à la table indicateur. Entrée : objet Indicateur ; sortie : sql

from dataclasses import asdict

from business_object.indicateur import Indicateur
from dao.db_connection import DBConnection


class IndicateurDAO:
    """
    Accès aux indicateurs dans la base de données.
    """

    def enregistrer(self, indicateur: Indicateur) -> int:
        """
        Enregistre un indicateur. S'il existe déjà (même code), ses informations
        sont mises à jour avec celles de la configuration.

        Returns:
            int: id de l'indicateur dans la base (utile pour enregistrer ses observations)
        """
        # with connection : commit si tout se passe bien, rollback en cas d'erreur
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO laborscope.indicateur (code, libelle, unite, frequence, nom_classif1) "
                    "VALUES (%(code)s, %(libelle)s, %(unite)s, %(frequence)s, %(nom_classif1)s) "
                    "ON CONFLICT (code) DO UPDATE SET "
                    "    libelle = EXCLUDED.libelle, "
                    "    unite = EXCLUDED.unite, "
                    "    frequence = EXCLUDED.frequence, "
                    "    nom_classif1 = EXCLUDED.nom_classif1 "
                    "RETURNING id;",
                    asdict(indicateur),  # {'code': 'EMP_...', 'libelle': '...', ...}
                )
                return cursor.fetchone()["id"]

    def lister(self) -> list[Indicateur]:
        """
        Liste tous les indicateurs enregistrés dans la base.

        Returns:
            list[Indicateur]: indicateurs triés par code
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT code, libelle, unite, frequence, nom_classif1 "
                    "FROM laborscope.indicateur ORDER BY code;"
                )
                lignes = cursor.fetchall()

        # chaque ligne est un dict {'code': ..., 'libelle': ...} : ** le transforme en arguments nommés
        return [Indicateur(**ligne) for ligne in lignes]

    def trouver_par_code(self, code: str) -> Indicateur | None:
        """
        Cherche un indicateur par son code.

        params:
            code: ex 'EMP_5EMP_SEX_OC2_NB_Q'

        Returns:
            Indicateur | None: l'indicateur, ou None s'il n'est pas dans la base
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT code, libelle, unite, frequence, nom_classif1 "
                    "FROM laborscope.indicateur WHERE code = %(code)s;",
                    {"code": code},
                )
                ligne = cursor.fetchone()  # None si aucune ligne

        return Indicateur(**ligne) if ligne else None
