"""
Faux comptes communs aux tests des controllers : un utilisateur simple, un administrateur,
et les en-têtes HTTP à envoyer pour être « connecté » en tant que l'un ou l'autre.

Utilisation : UtilisateurService.trouver_par_token est remplacé par TOKENS.get,
donc l'en-tête EN_TETE_ADMIN fait passer la requête pour celle de ADMIN.
"""

from business_object.utilisateur import Utilisateur

JDUPONT = Utilisateur(pseudo="jdupont", role="utilisateur", id=1)
ADMIN = Utilisateur(pseudo="admin", role="admin", id=2)

# Faux tokens : l'en-tête X-Auth-Token à envoyer pour être « connecté » en tant que...
EN_TETE_USER = {"X-Auth-Token": "token-user"}
EN_TETE_ADMIN = {"X-Auth-Token": "token-admin"}
TOKENS = {"token-user": JDUPONT, "token-admin": ADMIN}
