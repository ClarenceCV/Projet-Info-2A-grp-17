# Gardes du frontend : vérifier la session et protéger les pages.
# (inspiré du template ENSAI : frontend/src/utils/auth_guard.py, check_authentification)
#
# - verifier_session() : appelée par app.py à chaque exécution, AVANT de construire le menu
# - exiger_connexion() / exiger_admin() : à appeler tout en haut d'une page
#
# Utilisation dans une page :
#     from utils.auth_guard import exiger_connexion   # ou exiger_admin pour une page d'administration
#     exiger_connexion()
#
# Ce n'est pas la vraie sécurité : c'est l'API qui refuse les requêtes (401 / 403, c.f. backend
# controller/auth.py). Le frontend évite seulement d'afficher une page qui ne fonctionnerait pas.

import streamlit as st

from utils.api_client import api_client
from utils.session import oublier_session


def verifier_session():
    """
    Vérifie auprès de l'API que le token de la session est toujours valable
    (il ne l'est plus après un reset de la base, ou une déconnexion dans un autre onglet).
    - token refusé (401) : la session est oubliée, le menu redevient celui du visiteur ;
    - token accepté : pseudo et rôle sont mis à jour avec ceux de la base ;
    - API injoignable : on ne touche à rien (on ne déconnecte pas quelqu'un pour une panne).
    """
    if not st.session_state.get("token"):
        return  # personne n'est connecté : rien à vérifier

    reponse = api_client.get("/utilisateurs/moi")  # api_client envoie le token tout seul

    if reponse["status_code"] == 401:
        oublier_session()
        st.toast("Votre session a expiré : reconnectez-vous.", icon=":material/lock:")
    elif reponse["status_code"] == 200:
        st.session_state["pseudo"] = reponse["data"]["pseudo"]
        st.session_state["role"] = reponse["data"]["role"]


def exiger_connexion():
    """
    Arrête la page si personne n'est connecté (à appeler tout en haut de la page).
    """
    if not st.session_state.get("token"):
        st.warning("Connectez-vous pour accéder à cette page.")
        st.stop()  # rien de ce qui suit dans la page n'est exécuté


def exiger_admin():
    """
    Arrête la page si l'utilisateur n'est pas administrateur (à appeler tout en haut de la page).
    """
    exiger_connexion()
    if st.session_state.get("role") != "admin":
        st.error("Réservé aux administrateurs.")
        st.stop()
