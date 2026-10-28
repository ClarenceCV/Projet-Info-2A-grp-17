from dataclasses import dataclass
from datetime import datetime

# rôles possibles (même liste que la contrainte CHECK de la table utilisateur, c.f. data/init_db.sql)
ROLES = ("utilisateur", "admin")


@dataclass
class Utilisateur:
    """
    Utilisateur de l'application (une ligne de la table utilisateur).

    Le hash du mot de passe n'est volontairement PAS un attribut : il ne sort jamais de la couche
    DAO / service, et ne risque donc pas d'être renvoyé par l'API ou affiché par erreur.

    Attributes:
        pseudo (str): identifiant de connexion, ex : 'jdupont'
        role (str): 'utilisateur' ou 'admin'
        id (int | None): identifiant en base, None tant que l'utilisateur n'est pas enregistré
        date_creation (datetime | None): date de création du compte (remplie par la base)
    """

    pseudo: str
    role: str = "utilisateur"
    id: int | None = None
    date_creation: datetime | None = None

    def __post_init__(self):
        """Vérifie les attributs juste après la création de l'objet"""
        if not isinstance(self.pseudo, str) or not self.pseudo:
            raise ValueError("pseudo should be a non empty string")
        if self.role not in ROLES:
            raise ValueError(f"role should be one of {ROLES}")

    @property
    def est_admin(self) -> bool:
        """True si l'utilisateur est administrateur"""
        return self.role == "admin"

    def __str__(self):
        return f"{self.pseudo} ({self.role})"
