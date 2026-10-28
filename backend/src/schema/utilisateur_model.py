# Format JSON des utilisateurs échangé entre le backend et ses clients (navigateur, frontend).
# On sépare ce que le client ENVOIE (avec le mot de passe) de ce que l'API RENVOIE (jamais de mot de passe)
# (même principe que PlayerModel / PlayerReadModel dans le template ENSAI)

from datetime import datetime

from pydantic import BaseModel

# ---------------------------------------------------------------------------------------
# Entrées : corps des requêtes envoyées par le client
# ---------------------------------------------------------------------------------------


class IdentifiantsModel(BaseModel):
    """
    Pseudo et mot de passe : pour créer un compte (POST /utilisateurs) ou se connecter (POST /login).
    ex : {"pseudo": "jdupont", "mot_de_passe": "motdepasse123"}
    """

    pseudo: str
    mot_de_passe: str


# ---------------------------------------------------------------------------------------
# Sorties : ce que l'API renvoie (jamais de mot de passe ni de hash)
# ---------------------------------------------------------------------------------------


class UtilisateurModel(BaseModel):
    """
    Utilisateur renvoyé par l'API.
    ex : {"id": 1, "pseudo": "jdupont", "role": "utilisateur", "date_creation": "2026-10-28T14:05:00"}
    """

    id: int
    pseudo: str
    role: str
    date_creation: datetime | None = None


class ConnexionModel(BaseModel):
    """
    Réponse d'une connexion réussie : le token à renvoyer dans l'en-tête X-Auth-Token
    des requêtes suivantes, et l'utilisateur connecté.
    ex : {"token": "2fI98W0qFDN6...", "utilisateur": {"id": 1, "pseudo": "jdupont", ...}}
    """

    token: str
    utilisateur: UtilisateurModel
