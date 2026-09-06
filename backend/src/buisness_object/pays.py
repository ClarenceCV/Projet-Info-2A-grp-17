class Pays:
    """
    Classe pour les pays
    Attributes:
        code_iso (str): code unique pour identifier le pays.
        nom_pays (str): nom du pays

    """
    def __init__(
        self,
        code_iso: str,
        nom_pays: str
    ):
        """Constructor"""

        if not isinstance(code_iso, str):
            raise TypeError("code_iso should be a string")
        if not isinstance(nom_pays, str):
            raise TypeError("nom_pays should be a string")
        if not code_iso:
            raise ValueError("code_iso should not be empty")
        if not nom_pays:
            raise ValueError("nom_pays should not be empty")

        self.code_iso = code_iso
        self.nom_pays = nom_pays

    def __repr__(self):
        return f"Pays(code_iso={self.code_iso!r}, nom_pays={self.nom_pays!r})"

    def __eq__(self, other):
        if not isinstance(other, Pays):
            return NotImplemented
        return self.code_iso == other.code_iso and self.nom_pays == other.nom_pays

    def __hash__(self):
        return hash((self.code_iso, self.nom_pays))
