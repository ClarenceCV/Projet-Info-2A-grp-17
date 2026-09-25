class Profession:
    '''
    Profession object
    Attributes:
        libelle_profession (str): Name of the profession.
        id_profession (int | None): Unique identifier of the profession in the database,
            None until the profession is saved.
    '''
    def __init__(
        self,
        libelle_profession: str,
        id_profession: int | None = None
    ):
        """Constructor"""
        if id_profession is not None and not isinstance(id_profession, int):
            raise TypeError("Id should be an integer or None")
        if not isinstance(libelle_profession, str):
            raise TypeError("Libelle should be an chain of characters")

        self.id_profession = id_profession
        self.libelle_profession = libelle_profession
