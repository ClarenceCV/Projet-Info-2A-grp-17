# Tests du service des utilisateurs (F6) et du hachage des mots de passe.
# Le DAO est remplacé par un faux (patch.object) : les tests ne dépendent pas de la base.
# Avec un faux DAO, on peut aussi vérifier COMMENT le service l'a appelé (assert_called_once_with).
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests

from unittest.mock import patch

import pytest

from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDAO
from service.journal_service import JournalService
from service.utilisateur_service import UtilisateurService
from utils.securite import hacher_mdp, verifier_mdp

JDUPONT = Utilisateur(pseudo="jdupont", role="utilisateur", id=1)


@pytest.fixture(autouse=True)
def faux_journal():
    """
    Exécutée automatiquement avant CHAQUE test du fichier (autouse=True) : le journal est remplacé
    par un faux, pour ne pas écrire dans une vraie base. Le test peut le recevoir en paramètre
    pour vérifier ce qui a été noté.
    """
    with patch.object(JournalService, "enregistrer") as faux:
        yield faux  # le test s'exécute ici ; le vrai journal revient après


# --- Hachage ------------------------------------------------------------------------------


def test_hash_different_du_mot_de_passe():
    # WHEN
    mdp_hash = hacher_mdp("motdepasse123")
    # THEN : un hash bcrypt, qui ne contient pas le mot de passe
    assert mdp_hash != "motdepasse123"
    assert mdp_hash.startswith("$2b$")
    assert "motdepasse123" not in mdp_hash


def test_meme_mot_de_passe_hash_different():
    # WHEN : deux hachages du même mot de passe
    # THEN : hashs différents (sel aléatoire), mais tous les deux valides
    hash_1, hash_2 = hacher_mdp("motdepasse123"), hacher_mdp("motdepasse123")
    assert hash_1 != hash_2
    assert verifier_mdp("motdepasse123", hash_1)
    assert verifier_mdp("motdepasse123", hash_2)


def test_verifier_mauvais_mot_de_passe():
    assert not verifier_mdp("mauvais", hacher_mdp("motdepasse123"))


# --- Création de compte -------------------------------------------------------------------


def test_creer_compte_enregistre_un_hash():
    # GIVEN
    with patch.object(UtilisateurDAO, "creer", return_value=JDUPONT) as faux_creer:
        # WHEN
        res = UtilisateurService().creer_compte("  jdupont ", "motdepasse123")
    # THEN : le DAO a reçu le pseudo nettoyé et un hash (pas le mot de passe) qui correspond
    assert res == JDUPONT
    pseudo, mdp_hash, role = faux_creer.call_args.args
    assert pseudo == "jdupont"
    assert mdp_hash != "motdepasse123"
    assert verifier_mdp("motdepasse123", mdp_hash)
    assert role == "utilisateur"


def test_creer_compte_pseudo_deja_pris():
    # GIVEN : le DAO renvoie None (contrainte UNIQUE en base)
    with patch.object(UtilisateurDAO, "creer", return_value=None):
        # WHEN / THEN
        assert UtilisateurService().creer_compte("jdupont", "motdepasse123") is None


@pytest.mark.parametrize(
    "pseudo, mot_de_passe",
    [
        ("jdupont", "court"),        # mot de passe < 8 caractères
        ("jdupont", "x" * 73),       # mot de passe > 72 octets
        ("   ", "motdepasse123"),    # pseudo vide
        ("x" * 31, "motdepasse123"), # pseudo trop long
    ],
)
def test_creer_compte_refuse_les_valeurs_invalides(pseudo, mot_de_passe):
    # GIVEN : le DAO ne doit jamais être appelé
    with patch.object(UtilisateurDAO, "creer") as faux_creer:
        # WHEN / THEN
        with pytest.raises(ValueError):
            UtilisateurService().creer_compte(pseudo, mot_de_passe)
    faux_creer.assert_not_called()


# --- Connexion / déconnexion --------------------------------------------------------------


def test_se_connecter_ok():
    # GIVEN : un compte dont le mot de passe est 'motdepasse123'
    with patch.object(UtilisateurDAO, "lire_mdp_hash", return_value=hacher_mdp("motdepasse123")), \
         patch.object(UtilisateurDAO, "trouver_par_pseudo", return_value=JDUPONT), \
         patch.object(UtilisateurDAO, "enregistrer_token") as faux_token:
        # WHEN
        utilisateur, token = UtilisateurService().se_connecter("jdupont", "motdepasse123")
    # THEN : un token a été généré et enregistré pour cet utilisateur
    assert utilisateur == JDUPONT
    assert len(token) >= 40
    faux_token.assert_called_once_with(1, token)


def test_se_connecter_mauvais_mot_de_passe():
    with patch.object(UtilisateurDAO, "lire_mdp_hash", return_value=hacher_mdp("motdepasse123")), \
         patch.object(UtilisateurDAO, "enregistrer_token") as faux_token:
        assert UtilisateurService().se_connecter("jdupont", "mauvais") is None
    faux_token.assert_not_called()  # aucune session ouverte


def test_se_connecter_pseudo_inconnu():
    with patch.object(UtilisateurDAO, "lire_mdp_hash", return_value=None):
        assert UtilisateurService().se_connecter("personne", "motdepasse123") is None


def test_deux_connexions_deux_tokens_differents():
    with patch.object(UtilisateurDAO, "lire_mdp_hash", return_value=hacher_mdp("motdepasse123")), \
         patch.object(UtilisateurDAO, "trouver_par_pseudo", return_value=JDUPONT), \
         patch.object(UtilisateurDAO, "enregistrer_token"):
        _, token_1 = UtilisateurService().se_connecter("jdupont", "motdepasse123")
        _, token_2 = UtilisateurService().se_connecter("jdupont", "motdepasse123")
    assert token_1 != token_2


def test_se_deconnecter_efface_le_token():
    with patch.object(UtilisateurDAO, "enregistrer_token", return_value=True) as faux_token:
        assert UtilisateurService().se_deconnecter(JDUPONT)
    faux_token.assert_called_once_with(1, None)


# --- Administration -----------------------------------------------------------------------

ADMIN = Utilisateur(pseudo="admin", role="admin", id=2)


def test_supprimer_un_autre_compte():
    with patch.object(UtilisateurDAO, "supprimer", return_value=True) as faux_supprimer:
        assert UtilisateurService().supprimer(ADMIN, 1)
    faux_supprimer.assert_called_once_with(1)


def test_supprimer_compte_inexistant():
    with patch.object(UtilisateurDAO, "supprimer", return_value=False):
        assert not UtilisateurService().supprimer(ADMIN, 999)


def test_admin_ne_peut_pas_se_supprimer_lui_meme():
    # GIVEN : le DAO ne doit jamais être appelé
    with patch.object(UtilisateurDAO, "supprimer") as faux_supprimer:
        # WHEN / THEN
        with pytest.raises(ValueError):
            UtilisateurService().supprimer(ADMIN, ADMIN.id)
    faux_supprimer.assert_not_called()


def test_creer_compte_admin():
    with patch.object(UtilisateurDAO, "creer", return_value=ADMIN) as faux_creer:
        UtilisateurService().creer_compte("admin2", "motdepasse123", role="admin")
    assert faux_creer.call_args.args[2] == "admin"


# --- Journal ------------------------------------------------------------------------------


def test_connexion_notee_au_journal(faux_journal):
    with patch.object(UtilisateurDAO, "lire_mdp_hash", return_value=hacher_mdp("motdepasse123")), \
         patch.object(UtilisateurDAO, "trouver_par_pseudo", return_value=JDUPONT), \
         patch.object(UtilisateurDAO, "enregistrer_token"):
        UtilisateurService().se_connecter("jdupont", "motdepasse123")
    faux_journal.assert_called_once_with(JDUPONT, "connexion")


def test_echec_connexion_note_avec_le_pseudo_essaye(faux_journal):
    with patch.object(UtilisateurDAO, "lire_mdp_hash", return_value=None):
        UtilisateurService().se_connecter("pirate", "motdepasse123")
    faux_journal.assert_called_once_with(None, "echec_connexion", pseudo="pirate")


def test_creation_par_un_admin_notee_au_nom_de_l_admin(faux_journal):
    with patch.object(UtilisateurDAO, "creer", return_value=JDUPONT):
        UtilisateurService().creer_compte("jdupont", "motdepasse123", auteur=ADMIN)
    assert faux_journal.call_args.args[:2] == (ADMIN, "creation_compte")


def test_creation_refusee_rien_au_journal(faux_journal):
    with patch.object(UtilisateurDAO, "creer", return_value=None):  # pseudo déjà pris
        UtilisateurService().creer_compte("jdupont", "motdepasse123")
    faux_journal.assert_not_called()


# --- Premier administrateur (initialiser_admin, appelé au lancement de l'API) -------------


def test_initialiser_admin_cree_un_admin_s_il_n_y_en_a_pas():
    # GIVEN : la base ne contient qu'un utilisateur simple
    with patch.object(UtilisateurDAO, "lister", return_value=[JDUPONT]), \
         patch.object(UtilisateurService, "creer_compte") as faux_creer:
        # WHEN
        UtilisateurService().initialiser_admin()
    # THEN : un compte admin est créé
    faux_creer.assert_called_once()
    assert faux_creer.call_args.kwargs["role"] == "admin"


def test_initialiser_admin_ne_fait_rien_si_un_admin_existe():
    with patch.object(UtilisateurDAO, "lister", return_value=[JDUPONT, ADMIN]), \
         patch.object(UtilisateurService, "creer_compte") as faux_creer:
        UtilisateurService().initialiser_admin()
    faux_creer.assert_not_called()  # relancer l'API ne crée pas de doublon
