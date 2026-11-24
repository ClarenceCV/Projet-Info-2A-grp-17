""" Format JSON des indicateurs échangé entre le backend et ses clients (navigateur, frontend). """

from pydantic import BaseModel

# IndicateurModel reprend volontairement les champs de business_object.Indicateur : l'un est le
# format de l'API, l'autre l'objet métier (couches séparées). Ce n'est pas du code copié-collé.
# pylint: disable=duplicate-code


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


class IndicateurClassif1Model(BaseModel):
    """
    Modèle pour renvoyer les modalités d'un indicateur (profession ou tranche d'âge).
    """
    code: str
    modalites: list[str]
