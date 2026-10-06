from dataclasses import dataclass

#le décorateur dataclass permet de coder les méthodes init, repr et eq de la manière naturelle
@dataclass(frozen=True) # le frozen fixe les indicateurs (pas de modifications après la création)
class Indicateur:
    """
    Indicateur ILOSTAT (pour l'instant on en a 2).

    Attributes:
        code (str): identifiant du dataset dans l'API, ex : 'EMP_5EMP_SEX_OC2_NB_Q'
        libelle (str): nom lisible affiché à l'utilisateur, ex : 'Emploi par sexe et profession'
        unite (str): unité des valeurs, 'milliers' ou '%'
        frequence (str): 'Q' (trimestriel), 'A' (annuel) ou 'M' (mensuel)
        nom_classif1 (str | None): ce que contient la colonne classif1, ex : 'profession'
    """

    code: str
    libelle: str
    unite: str
    frequence: str
    nom_classif1: str | None = None

    def __post_init__(self):
        """Vérifie les attributs juste après la création de l'objet"""
        for nom in ("code", "libelle", "unite"):
            valeur = getattr(self, nom)
            if not isinstance(valeur, str) or not valeur:
                raise ValueError(f"{nom} should be a non empty string")
        if self.frequence not in ("Q", "A", "M"):
            raise ValueError("frequence should be 'Q', 'A' or 'M'")
        if self.nom_classif1 is not None and not isinstance(self.nom_classif1, str):
            raise TypeError("nom_classif1 should be a string or None")

    def __str__(self):
        return f"{self.libelle} ({self.unite})"
