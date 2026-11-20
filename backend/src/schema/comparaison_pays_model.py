""" Format JSON de la comparaison entre pays (F4) échangé entre le backend et ses clients. """

from pydantic import BaseModel

from schema.pays_model import PaysClasseModel


class ComparaisonPaysModel(BaseModel):
    """
    Résultat de la comparaison entre pays : le classement complet, les plus hauts et les plus bas.
    periode_reference vaut null s'il n'y a aucune donnée.
    """

    periode_reference: str | None
    classement: list[PaysClasseModel]
    plus_hauts: list[PaysClasseModel]
    plus_bas: list[PaysClasseModel]
