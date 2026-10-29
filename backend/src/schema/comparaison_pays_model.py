# Format JSON de la comparaison entre pays (F4) échangé entre le backend et ses clients.

from pydantic import BaseModel


class PaysClasseModel(BaseModel):
    """
    Un pays du classement.
    ex : {"rang": 1, "code_iso": "DEU", "nom_pays": "Germany", "periode": "2024Q4",
          "valeur": 61.2, "unite": "%"}
    """

    rang: int
    code_iso: str
    nom_pays: str
    periode: str
    valeur: float
    unite: str


class ComparaisonPaysModel(BaseModel):
    """
    Résultat de la comparaison entre pays : le classement complet, les plus hauts et les plus bas.
    periode_reference vaut null s'il n'y a aucune donnée.
    """

    periode_reference: str | None
    classement: list[PaysClasseModel]
    plus_hauts: list[PaysClasseModel]
    plus_bas: list[PaysClasseModel]
