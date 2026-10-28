# Logique métier des comptes utilisateurs (F6) : création, connexion, déconnexion.
# Le controller appelle le service, le service appelle le DAO.

import secrets

from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDAO
from utils.securite import hacher_mdp, verifier_mdp

LONGUEUR_MIN_MDP = 8
LONGUEUR_MAX_MDP = 72  # en octets : limite de bcrypt
LONGUEUR_MAX_PSEUDO = 30


class UtilisateurService:
    """
    Service des utilisateurs.
    """

    def creer_compte(self, pseudo: str, mot_de_passe: str, role: str = "utilisateur") -> Utilisateur | None:
        """
        Crée un compte : vérifie le pseudo et le mot de passe, hache le mot de passe, enregistre.

        params:
            pseudo: identifiant de connexion (espaces au début et à la fin retirés)
            mot_de_passe: mot de passe en clair (jamais enregistré tel quel)
            role: 'utilisateur' (par défaut) ou 'admin' (seul un admin pourra créer un admin)

        Returns:
            Utilisateur | None: le compte créé, ou None si le pseudo est déjà pris

        Raises:
            ValueError: pseudo ou mot de passe invalide (message à afficher à l'utilisateur)
        """
        pseudo = pseudo.strip()
        if not pseudo or len(pseudo) > LONGUEUR_MAX_PSEUDO:
            raise ValueError(f"Le pseudo doit contenir entre 1 et {LONGUEUR_MAX_PSEUDO} caractères.")
        if len(mot_de_passe) < LONGUEUR_MIN_MDP:
            raise ValueError(f"Le mot de passe doit contenir au moins {LONGUEUR_MIN_MDP} caractères.")
        if len(mot_de_passe.encode("utf-8")) > LONGUEUR_MAX_MDP:
            raise ValueError("Le mot de passe est trop long (72 octets maximum).")

        return UtilisateurDAO().creer(pseudo, hacher_mdp(mot_de_passe), role)

    def se_connecter(self, pseudo: str, mot_de_passe: str) -> tuple[Utilisateur, str] | None:
        """
        Vérifie les identifiants et, s'ils sont bons, ouvre une session (nouveau token).

        Returns:
            tuple[Utilisateur, str] | None: l'utilisateur et son token,
                ou None si le pseudo n'existe pas OU si le mot de passe est faux
                (on ne dit pas lequel des deux : ça aiderait un attaquant à deviner les pseudos)
        """
        dao = UtilisateurDAO()
        mdp_hash = dao.lire_mdp_hash(pseudo.strip())
        if mdp_hash is None or not verifier_mdp(mot_de_passe, mdp_hash):
            return None

        utilisateur = dao.trouver_par_pseudo(pseudo.strip())
        token = secrets.token_urlsafe(32)  # 32 octets aléatoires → ~43 caractères, impossible à deviner
        dao.enregistrer_token(utilisateur.id, token)
        return utilisateur, token

    def se_deconnecter(self, utilisateur: Utilisateur) -> bool:
        """
        Ferme la session : le token est effacé, il ne fonctionnera plus.

        Returns:
            bool: True si la déconnexion a été enregistrée
        """
        return UtilisateurDAO().enregistrer_token(utilisateur.id, None)

    def trouver_par_token(self, token: str | None) -> Utilisateur | None:
        """
        Retrouve l'utilisateur connecté à partir de son token (utilisé par les gardes de controller/auth.py).

        Returns:
            Utilisateur | None: None si le token est absent, inconnu ou effacé (déconnexion)
        """
        return UtilisateurDAO().trouver_par_token(token)
