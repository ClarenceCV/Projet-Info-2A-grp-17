# Format JSON des indicateurs échangé entre le backend et ses clients (navigateur, frontend).

from pydantic import BaseModel


class IndicateurModel(BaseModel):
    """
    Indicateur renvoyé par l'API.
    ex : {"code": "EMP_5EMP_SEX_OC2_NB_Q", "libelle": "Emploi par sexe et profession",
          "unite": "milliers", "frequence": "Q", "nom_classif1": "profession"}
    """

    code: str
    libelle: str
    unite: str
    frequence: str
    nom_classif1: str | None = None
