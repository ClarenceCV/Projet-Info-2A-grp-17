from pydantic import BaseModel


class Pays(BaseModel):
    """
    Pays renvoyé par l'API
    ex: { code_iso: "FRA", nom_pays: "France", continent: "EU" | None }
    """

    code_iso = str
    nom_pays = str
    continent = str | None
