# Comptes créés automatiquement à chaque réinitialisation de la base (c.f. utils/reset_database.py),
# pour pouvoir se connecter tout de suite pendant le développement et la soutenance :
#     user  / user   → utilisateur
#     admin / admin  → administrateur
# Nécessaire car personne ne peut devenir admin via l'API (POST /utilisateurs crée des utilisateurs
# simples, et seul un admin peut créer d'autres admins).
#
# ⚠️ Mots de passe volontairement simples : ils ne respectent pas la règle des 8 caractères
# (UtilisateurService.creer_compte). On passe donc directement par le DAO, avec le même hachage bcrypt.
# Pour une vraie mise en ligne, il faudrait les supprimer ou changer leurs mots de passe.
#
# Lancement seul (depuis backend/src), sans réinitialiser la base :
#     uv run python -m utils.comptes_par_defaut

import dotenv

from dao.utilisateur_dao import UtilisateurDAO
from utils.securite import hacher_mdp

# (pseudo, mot de passe, rôle)
COMPTES_PAR_DEFAUT = [
    ("user", "user", "utilisateur"),
    ("admin", "admin", "admin"),
]


def creer_comptes_par_defaut():
    """
    Crée les comptes par défaut. Ceux qui existent déjà sont laissés tels quels
    (le script peut donc être relancé sans risque).
    """
    for pseudo, mot_de_passe, role in COMPTES_PAR_DEFAUT:
        compte = UtilisateurDAO().creer(pseudo, hacher_mdp(mot_de_passe), role)
        if compte is None:  # contrainte UNIQUE : le pseudo existe déjà
            print(f"  - {pseudo:<6} : existe déjà")
        else:
            print(f"  - {pseudo:<6} : créé ({role}, mot de passe '{mot_de_passe}')")


if __name__ == "__main__":
    dotenv.load_dotenv(override=True)  # charge le .env avant la connexion
    print("Comptes par défaut :")
    creer_comptes_par_defaut()
