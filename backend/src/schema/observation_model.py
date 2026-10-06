# Format JSON des observations échangé entre le backend et ses clients (navigateur, frontend).

from pydantic import BaseModel


class ObservationModel(BaseModel):
    """
    Observation renvoyée par l'API.
    ex : {"indicateur": "EMP_5WAP_SEX_AGE_RT_Q", "code_iso": "FRA", "nom_pays": "France",
          "source": "LFS - Employment Survey", "periode": "2024Q4", "sexe": "Female",
          "classif1": "15-24", "valeur": 31.2, "unite": "%", "statut": null}
    """

    indicateur: str
    code_iso: str
    nom_pays: str
    source: str
    periode: str
    sexe: str
    classif1: str
    valeur: float
    unite: str
    statut: str | None = None
