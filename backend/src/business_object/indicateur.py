class Indicateur:
    """
    Classe pour les indicateurs ILOSTAT
    Attributes:
        code_ilostat (str): code unique de l'indicateur (ex : 'EMP_5EMP_SEX_OC2_NB_Q')
        libelle (str): nom lisible de l'indicateur
        unite (str): unité des valeurs ('milliers' ou '%')
        description (str | None): description détaillée
        id_indicateur (int | None): identifiant en base, None tant que non enregistré
    """

    def __init__(
        self,
        code_ilostat: str,
        libelle: str,
        unite: str,
        description: str | None = None,
        id_indicateur: int | None = None,
    ):
        """Constructor"""
        if not isinstance(code_ilostat, str) or not code_ilostat:
            raise ValueError("code_ilostat should be a non empty string")
        if not isinstance(libelle, str) or not libelle:
            raise ValueError("libelle should be a non empty string")
        if not isinstance(unite, str) or not unite:
            raise ValueError("unite should be a non empty string")
        if description is not None and not isinstance(description, str):
            raise TypeError("description should be a string or None")
        if id_indicateur is not None and not isinstance(id_indicateur, int):
            raise TypeError("id_indicateur should be an integer or None")

        self.code_ilostat = code_ilostat
        self.libelle = libelle
        self.unite = unite
        self.description = description
        self.id_indicateur = id_indicateur

    def __str__(self):
        return f"{self.libelle} ({self.unite})"

    def __repr__(self):
        return f"Indicateur(code_ilostat={self.code_ilostat!r}, libelle={self.libelle!r})"

    def __eq__(self, other):
        if not isinstance(other, Indicateur):
            return NotImplemented
        return self.code_ilostat == other.code_ilostat

    def __hash__(self):
        return hash(self.code_ilostat)
