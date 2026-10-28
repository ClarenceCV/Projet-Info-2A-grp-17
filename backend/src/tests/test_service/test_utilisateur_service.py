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
from service.utilisateur_service import UtilisateurService
from utils.securite import hacher_mdp, verifier_mdp

JDUPONT = Utilisateur(pseudo="jdupont", role="utilisateur", id=1)


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
