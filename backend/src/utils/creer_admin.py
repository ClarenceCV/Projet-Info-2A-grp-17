# Crée le premier administrateur, dont le pseudo et le mot de passe sont lus dans le .env :
#     ADMIN_PSEUDO=...
#     ADMIN_MDP=...
# Nécessaire car personne ne peut devenir admin via l'API (POST /utilisateurs crée des utilisateurs
# simples, et seul un admin pourra créer d'autres admins).
# À relancer après chaque utils.reset_database (le reset supprime aussi les comptes).
#
# Lancement (depuis backend/src) :
#     uv run python -m utils.creer_admin

import os
import sys

import dotenv

from service.utilisateur_service import UtilisateurService


def creer_admin() -> bool:
    """
    Crée le compte administrateur décrit dans le .env (en passant par le service :
    mêmes règles et même hachage bcrypt qu'un compte créé par l'API).

    Returns:
        bool: True si l'administrateur existe à la fin (créé maintenant ou déjà présent)
    """
    pseudo = os.getenv("ADMIN_PSEUDO")
    mot_de_passe = os.getenv("ADMIN_MDP")
    if not pseudo or not mot_de_passe:
        print("ADMIN_PSEUDO et ADMIN_MDP doivent être renseignés dans le fichier .env")
        return False

    try:
        admin = UtilisateurService().creer_compte(pseudo, mot_de_passe, role="admin")
    except ValueError as e:  # mot de passe trop court...
        print(f"Administrateur non créé : {e}")
        return False

    if admin is None:  # le pseudo existe déjà : rien à faire
        print(f"Le compte '{pseudo}' existe déjà.")
    else:
        print(f"Administrateur créé : {admin}")
    return True


if __name__ == "__main__":
    dotenv.load_dotenv(override=True)  # charge le .env avant la connexion
    # code de sortie 1 en cas d'échec (utile si le script est enchaîné avec d'autres commandes)
    sys.exit(0 if creer_admin() else 1)
