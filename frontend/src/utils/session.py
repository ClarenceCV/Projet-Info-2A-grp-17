"""Session de l'utilisateur côté frontend : ouvrir et fermer une connexion.
L'utilisateur connecté est gardé dans st.session_state, qui survit aux réexécutions du script :
    st.session_state["token"]   : envoyé à l'API par api_client (en-tête X-Auth-Token)
    st.session_state["pseudo"]  : affiché dans le menu
    st.session_state["role"]    : 'utilisateur' ou 'admin', choisit le menu (c.f. app.py)
"""

from typing import Any

import streamlit as st

from utils.api_client import api_client


def message_erreur(reponse: dict) -> str:
    """
    Extrait un message lisible d'une réponse en erreur de api_client.

    Returns:
        str: le message « backend injoignable » (status_code 0), sinon le message du backend
        (champ 'detail'), ou à défaut le contenu de la réponse
    """
    donnees = reponse["data"]
    if reponse["status_code"] == 0:  # backend injoignable : api_client a mis le message dans data
        return donnees
    if isinstance(donnees, dict) and isinstance(donnees.get("detail"), str):
        return donnees["detail"]
    return f"Erreur {reponse['status_code']} : {donnees}"


def donnees_ou_arret(reponse: dict) -> Any:
    """
    Renvoie les données d'une réponse réussie (code 200). Sinon, affiche l'erreur et arrête la page
    (st.stop() : rien de ce qui suit dans la page ne s'exécute).

    Utilisation dans une page :
        donnees = donnees_ou_arret(api_client.get("/analyses/evolution", params=...))
    """
    if reponse["status_code"] != 200:
        st.error(message_erreur(reponse))
        st.stop()
    return reponse["data"]


def connecter(pseudo: str, mot_de_passe: str) -> str | None:
    """
    Demande une connexion à l'API et, si elle réussit, garde l'utilisateur dans la session.

    Returns:
        str | None: None si la connexion a réussi, sinon le message d'erreur à afficher
    """
    reponse = api_client.post("/login", json={"pseudo": pseudo, "mot_de_passe": mot_de_passe})

    if reponse["status_code"] == 200:
        st.session_state["token"] = reponse["data"]["token"]
        st.session_state["pseudo"] = reponse["data"]["utilisateur"]["pseudo"]
        st.session_state["role"] = reponse["data"]["utilisateur"]["role"]
        return None
    return message_erreur(reponse)


def connecter_et_ouvrir_accueil(pseudo: str, mot_de_passe: str):
    """Connecte l'utilisateur puis ouvre l'accueil ; en cas d'échec, affiche l'erreur."""
    erreur = connecter(pseudo, mot_de_passe)
    if erreur:
        st.error(erreur)
    else:
        st.switch_page("pages/accueil.py")  # app.py reconstruit le menu selon le rôle


def oublier_session():
    """Efface l'utilisateur de la session Streamlit (sans appeler l'API)."""
    for cle in ("token", "pseudo", "role"):
        st.session_state.pop(cle, None)


def deconnecter():
    """
    Ferme la session : le token est invalidé par l'API, puis oublié par le frontend.
    Utilisée comme callback d'un bouton (on_click) : exécutée avant la réexécution du script.
    """
    api_client.post("/logout")  # avant d'oublier le token : l'API en a besoin pour savoir qui part
    oublier_session()  # même si l'API est injoignable : on ne reste pas connecté à l'écran
