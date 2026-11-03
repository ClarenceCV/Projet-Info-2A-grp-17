# Logique métier des comptes utilisateurs (F6) : création, connexion, déconnexion.
# Le controller appelle le service, le service appelle le DAO.
# Chaque action est notée dans le journal (c.f. service/journal_service.py).

import secrets

from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDAO
from service.journal_service import JournalService
from utils.securite import hacher_mdp, verifier_mdp

LONGUEUR_MIN_MDP = 8
LONGUEUR_MAX_MDP = 72  # en octets : limite de bcrypt
LONGUEUR_MAX_PSEUDO = 30


class UtilisateurService:
    """
    Service des utilisateurs.
    """

    def creer_compte(
        self, pseudo: str, mot_de_passe: str, role: str = "utilisateur", auteur: Utilisateur | None = None
    ) -> Utilisateur | None:
        """
        Crée un compte : vérifie le pseudo et le mot de passe, hache le mot de passe, enregistre.

        params:
            pseudo: identifiant de connexion (espaces au début et à la fin retirés)
            mot_de_passe: mot de passe en clair (jamais enregistré tel quel)
            role: 'utilisateur' (par défaut) ou 'admin' (seul un admin pourra créer un admin)
            auteur: l'administrateur qui crée le compte (None : la personne crée son propre compte)

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

        utilisateur = UtilisateurDAO().creer(pseudo, hacher_mdp(mot_de_passe), role)
        if utilisateur is not None:
            if auteur is None:  # inscription : c'est le nouveau compte qui fait l'action
                JournalService().enregistrer(utilisateur, "creation_compte", f"rôle {role}")
            else:  # création par un administrateur
                JournalService().enregistrer(auteur, "creation_compte", f"compte « {pseudo} », rôle {role}")
        return utilisateur

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
            # utile pour repérer des tentatives répétées sur un même compte
            JournalService().enregistrer(None, "echec_connexion", pseudo=pseudo.strip())
            return None

        utilisateur = dao.trouver_par_pseudo(pseudo.strip())
        token = secrets.token_urlsafe(32)  # 32 octets aléatoires → ~43 caractères, impossible à deviner
        dao.enregistrer_token(utilisateur.id, token)
        JournalService().enregistrer(utilisateur, "connexion")
        return utilisateur, token

    def se_deconnecter(self, utilisateur: Utilisateur) -> bool:
        """
        Ferme la session : le token est effacé, il ne fonctionnera plus.

        Returns:
            bool: True si la déconnexion a été enregistrée
        """
        JournalService().enregistrer(utilisateur, "deconnexion")
        return UtilisateurDAO().enregistrer_token(utilisateur.id, None)

    def trouver_par_token(self, token: str | None) -> Utilisateur | None:
        """
        Retrouve l'utilisateur connecté à partir de son token (utilisé par les gardes de controller/auth.py).

        Returns:
            Utilisateur | None: None si le token est absent, inconnu ou effacé (déconnexion)
        """
        return UtilisateurDAO().trouver_par_token(token)

    # ------------------------------------------------------------------
    # Administration (réservé aux administrateurs, c.f. admin_utilisateur_controller)
    # ------------------------------------------------------------------
    def lister(self) -> list[Utilisateur]:
        """
        Returns:
            list[Utilisateur]: tous les comptes, triés par pseudo
        """
        return UtilisateurDAO().lister()

    def supprimer(self, admin: Utilisateur, id_utilisateur: int) -> bool:
        """
        Supprime un compte. Un administrateur ne peut pas supprimer son propre compte
        (sinon il pourrait ne plus rester aucun administrateur pour gérer l'application).

        params:
            admin: l'administrateur qui fait la demande
            id_utilisateur: id du compte à supprimer

        Returns:
            bool: True si le compte a été supprimé, False s'il n'existe pas

        Raises:
            ValueError: si l'administrateur essaie de supprimer son propre compte
        """
        if id_utilisateur == admin.id:
            raise ValueError("Vous ne pouvez pas supprimer votre propre compte.")
        supprime = UtilisateurDAO().supprimer(id_utilisateur)
        if supprime:
            JournalService().enregistrer(admin, "suppression_compte", f"compte n°{id_utilisateur}")
        return supprime

    def initialiser_admin(self):
        """
        Permet de créer un administrateur
        (utilisé dans main.py pour avoir ce compte admin dès le lancement de l'app)
        """
        utilisateurs = self.lister()

        admin_existe = any(u.role == "admin" for u in utilisateurs)

        if not admin_existe:
            self.creer_compte(
                pseudo="admin",
                mot_de_passe="admin123",
                role="admin"
            )
