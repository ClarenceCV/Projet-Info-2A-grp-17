# Endpoints de connexion (sans préfixe, c.f. main.py) : POST /login, POST /logout
# (repris du template ENSAI : backend/src/controller/login_controller.py)

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from business_object.utilisateur import Utilisateur
from controller.auth import utilisateur_connecte
from schema.utilisateur_model import ConnexionModel, IdentifiantsModel, UtilisateurModel
from service.utilisateur_service import UtilisateurService

router = APIRouter()


@router.post("/login", response_model=ConnexionModel)
def se_connecter(identifiants: IdentifiantsModel):
    """
    Vérifie le pseudo et le mot de passe, et renvoie un token de session.
    Le token est à envoyer dans l'en-tête HTTP X-Auth-Token des requêtes suivantes.
    Erreur 401 si les identifiants sont invalides.
    """
    resultat = UtilisateurService().se_connecter(identifiants.pseudo, identifiants.mot_de_passe)
    if resultat is None:
        # même message que le pseudo existe ou non (ne pas aider à deviner les pseudos)
        raise HTTPException(status_code=401, detail="Identifiants invalides.")

    utilisateur, token = resultat
    return ConnexionModel(token=token, utilisateur=UtilisateurModel(**asdict(utilisateur)))


@router.post("/logout")
def se_deconnecter(utilisateur: Utilisateur = Depends(utilisateur_connecte)):
    """
    Ferme la session de l'utilisateur connecté : son token ne fonctionnera plus.
    Erreur 401 si personne n'est connecté.
    """
    UtilisateurService().se_deconnecter(utilisateur)
    return {"message": f"Au revoir {utilisateur.pseudo}."}
