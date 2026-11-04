# Tests d'UtilisateurDAO sur la vraie base (pseudos 'test_dao...', supprimés après chaque test : c.f. conftest.py)
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_dao

from dao.utilisateur_dao import UtilisateurDAO

FAUX_HASH = "hash_de_test"  # le DAO ne vérifie pas le hash : c'est le rôle du service


def test_creer():
    # WHEN
    utilisateur = UtilisateurDAO().creer("test_dao_jean", FAUX_HASH)
    # THEN : l'utilisateur a un id et le rôle par défaut
    assert utilisateur.id is not None
    assert utilisateur.pseudo == "test_dao_jean"
    assert utilisateur.role == "utilisateur"


def test_creer_pseudo_deja_pris():
    # GIVEN
    dao = UtilisateurDAO()
    dao.creer("test_dao_jean", FAUX_HASH)
    # WHEN : même pseudo (contrainte UNIQUE)
    doublon = dao.creer("test_dao_jean", FAUX_HASH)
    # THEN
    assert doublon is None


def test_trouver_par_pseudo():
    # GIVEN
    dao = UtilisateurDAO()
    dao.creer("test_dao_admin", FAUX_HASH, role="admin")
    # WHEN
    utilisateur = dao.trouver_par_pseudo("test_dao_admin")
    # THEN
    assert utilisateur.role == "admin"


def test_trouver_par_pseudo_inconnu():
    # WHEN
    utilisateur = UtilisateurDAO().trouver_par_pseudo("test_dao_personne")
    # THEN
    assert utilisateur is None


def test_lire_mdp_hash():
    # GIVEN
    dao = UtilisateurDAO()
    dao.creer("test_dao_jean", FAUX_HASH)
    # WHEN / THEN
    assert dao.lire_mdp_hash("test_dao_jean") == FAUX_HASH
    assert dao.lire_mdp_hash("test_dao_personne") is None


def test_enregistrer_token_puis_trouver_par_token():
    # GIVEN
    dao = UtilisateurDAO()
    utilisateur = dao.creer("test_dao_jean", FAUX_HASH)
    # WHEN
    ok = dao.enregistrer_token(utilisateur.id, "test_dao_token")
    # THEN
    assert ok
    assert dao.trouver_par_token("test_dao_token").pseudo == "test_dao_jean"


def test_effacer_token():
    # GIVEN : un utilisateur connecté
    dao = UtilisateurDAO()
    utilisateur = dao.creer("test_dao_jean", FAUX_HASH)
    dao.enregistrer_token(utilisateur.id, "test_dao_token")
    # WHEN : déconnexion
    dao.enregistrer_token(utilisateur.id, None)
    # THEN : l'ancien token ne marche plus
    assert dao.trouver_par_token("test_dao_token") is None


def test_trouver_par_token_vide():
    # WHEN / THEN
    assert UtilisateurDAO().trouver_par_token(None) is None


def test_lister_contient_l_utilisateur():
    # GIVEN
    dao = UtilisateurDAO()
    dao.creer("test_dao_jean", FAUX_HASH)
    # WHEN
    pseudos = [utilisateur.pseudo for utilisateur in dao.lister()]
    # THEN
    assert "test_dao_jean" in pseudos


def test_supprimer():
    # GIVEN
    dao = UtilisateurDAO()
    utilisateur = dao.creer("test_dao_jean", FAUX_HASH)
    # WHEN
    ok = dao.supprimer(utilisateur.id)
    # THEN
    assert ok
    assert dao.trouver_par_pseudo("test_dao_jean") is None


def test_supprimer_id_inexistant():
    # WHEN
    ok = UtilisateurDAO().supprimer(-1)
    # THEN
    assert not ok
