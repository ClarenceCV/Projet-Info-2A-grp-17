from pydantic import BaseModel


class PaysModel(BaseModel):
    """
    Pays renvoyé par l'API
    ex: { code_iso: "FRA", nom_pays: "France", continent: "EU" | None }
    """

    code_iso: str
    nom_pays: str
