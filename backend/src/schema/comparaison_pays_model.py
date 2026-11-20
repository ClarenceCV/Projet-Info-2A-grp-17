""" Format JSON de la comparaison entre pays (F4) échangé entre le backend et ses clients. """

from pydantic import BaseModel

from schema.pays_model import PaysClasseModel


class ComparaisonPaysModel(BaseModel):
    """
    Résultat de la comparaison entre pays : le classement complet, les plus hauts et les plus bas.
    periode_reference vaut null s'il n'y a aucune donnée.
    periodes_disponibles : toutes les périodes de la base pour ces choix (pour le menu de la page).
    """

    periode_reference: str | None
    periodes_disponibles: list[str]
    periode_commune: str | None  # dernière période où tous les pays ont une donnée (null si aucune)
    classement: list[PaysClasseModel]
    plus_hauts: list[PaysClasseModel]
    plus_bas: list[PaysClasseModel]
