# Ce fichier centralise tout ce qui concerne les autorisations de connexion (admin/user)
# 
# Il y a don toutes les fonctions exécutées par FastAPI AVANT un endpoint (avec Depends)
# pour savoir qui fait la requête et s'il en a le droit.
#
# Utilisation dans un controller :
#     from fastapi import Depends
#     from controller.auth import utilisateur_connecte, admin_requis
#
#     @router.get("/...")
#     async def mon_endpoint(..., utilisateur=Depends(utilisateur_connecte)):   # connecté
#     async def mon_endpoint(..., utilisateur=Depends(admin_requis)):           # admin
#
# VERSION PROVISOIRE pour commencer à coder les différents users / admin :
# tout le monde passe, avec un administrateur fictif.
# La vraie vérification (token en base, 401 / 403) remplacera le contenu des fonctions,
# sans changer leur nom : les controllers qui les utilisent n'auront rien à modifier.

from fastapi import Depends, Header

# utilisateur renvoyé tant que la connexion n'existe pas
UTILISATEUR_FICTIF = {"pseudo": "dev", "role": "admin"}


def utilisateur_connecte(x_auth_token: str | None = Header(None)) -> dict:
    """
    Renvoie l'utilisateur qui fait la requête, à partir de son token.
    Le token est lu dans l'en-tête HTTP 'X-Auth-Token' (FastAPI fait la correspondance
    avec le nom du paramètre x_auth_token).

    Provisoire : renvoie toujours l'utilisateur fictif, avec ou sans token.

    Returns:
        dict: l'utilisateur connecté
    """
    return UTILISATEUR_FICTIF


def admin_requis(utilisateur: dict = Depends(utilisateur_connecte)) -> dict:
    """
    Vérifie que l'utilisateur connecté est administrateur.
    Dépend de utilisateur_connecte : FastAPI vérifie d'abord la connexion,
    puis appelle cette fonction avec l'utilisateur trouvé.

    Provisoire : laisse tout passer.

    Returns:
        dict: l'utilisateur connecté (administrateur)
    """
    return utilisateur
