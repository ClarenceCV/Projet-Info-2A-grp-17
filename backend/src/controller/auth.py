# Ce fichier centralise tout ce qui concerne les autorisations de connexion (admin/user)
#
# Il y a donc toutes les fonctions exécutées par FastAPI AVANT un endpoint (avec Depends)
# pour savoir qui fait la requête et s'il en a le droit.
#
# Utilisation dans un controller :
#     from fastapi import Depends
#     from controller.auth import utilisateur_connecte, admin_requis
#
#     @router.get("/...")
#     def mon_endpoint(..., utilisateur=Depends(utilisateur_connecte)):   # connecté (sinon 401)
#     def mon_endpoint(..., utilisateur=Depends(admin_requis)):           # admin (sinon 401 / 403)
#
# Le client envoie son token (obtenu avec POST /login) dans l'en-tête HTTP 'X-Auth-Token'.
# Dans /docs : bouton « Authorize » en haut à droite, coller le token une fois pour toutes.
# (inspiré du template ENSAI : verify_token dans backend/src/utils/security.py)

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from business_object.utilisateur import Utilisateur
from service.utilisateur_service import UtilisateurService

# Lecture de l'en-tête X-Auth-Token. APIKeyHeader (plutôt que Header) fait aussi apparaître
# le bouton « Authorize » dans /docs. auto_error=False : si l'en-tête manque, on reçoit None
# et c'est nous qui renvoyons l'erreur 401, avec notre message.
lecture_token = APIKeyHeader(
    name="X-Auth-Token",
    auto_error=False,
    description="Token obtenu avec POST /login",
)


def utilisateur_connecte(token: str | None = Security(lecture_token)) -> Utilisateur:
    """
    Renvoie l'utilisateur qui fait la requête, à partir de son token.

    Returns:
        Utilisateur: l'utilisateur connecté

    Raises:
        HTTPException 401: token absent, inconnu, ou effacé par une déconnexion
    """
    utilisateur = UtilisateurService().trouver_par_token(token)
    if utilisateur is None:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    return utilisateur


def admin_requis(utilisateur: Utilisateur = Depends(utilisateur_connecte)) -> Utilisateur:
    """
    Vérifie que l'utilisateur connecté est administrateur.
    Dépend de utilisateur_connecte : FastAPI vérifie d'abord la connexion (401),
    puis appelle cette fonction avec l'utilisateur trouvé.

    Returns:
        Utilisateur: l'utilisateur connecté (administrateur)

    Raises:
        HTTPException 403: l'utilisateur est connecté mais n'est pas administrateur
    """
    if not utilisateur.est_admin:
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs.")
    return utilisateur
