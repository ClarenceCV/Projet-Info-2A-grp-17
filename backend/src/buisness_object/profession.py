class Profession:
    '''
    Profession object
    Attributes:
        id_profession (int): Unique identifier pro the profession.
        libelle_profession (str): Name of the profession.
    '''
    def __init__(
        self,
        id_profession: int,
        libelle_profession: str
    ):
        """Constructor"""
        if not isinstance(id_profession, int):
            raise TypeError("Id should be an integer")
        if not isinstance(libelle_profession, str):
            raise TypeError("Libelle should be an chain of characters")

        self.id_profession = id_profession
        self.libelle_profession = libelle_profession
