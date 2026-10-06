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
