# Page « Créer un compte » : formulaire, puis connexion automatique.
# Endpoints utilisés : POST /utilisateurs, POST /login (via utils/session.py)
# Responsable : B

import streamlit as st

from utils.api_client import api_client
from utils.session import connecter, message_erreur

st.title("Créer un compte")

with st.form("formulaire_creation_compte"):
    pseudo = st.text_input("Pseudo")
    mot_de_passe = st.text_input("Mot de passe", type="password", help="8 caractères minimum")
    confirmation = st.text_input("Confirmer le mot de passe", type="password")
    envoye = st.form_submit_button("Créer mon compte", type="primary")

if envoye:
    # seule vérification du frontend : l'API ne connaît pas le champ de confirmation.
    # Les autres règles (longueurs, pseudo libre) sont vérifiées par le backend.
    if mot_de_passe != confirmation:
        st.error("Les deux mots de passe sont différents.")
    else:
        reponse = api_client.post(
            "/utilisateurs", json={"pseudo": pseudo, "mot_de_passe": mot_de_passe}
        )
        if reponse["status_code"] == 201:
            erreur = connecter(pseudo, mot_de_passe)  # on évite de lui redemander ses identifiants
            if erreur:
                st.error(erreur)
            else:
                st.switch_page("pages/accueil.py")
        elif reponse["status_code"] == 0:  # backend injoignable
            st.error(reponse["data"])
        else:  # 400 : pseudo pris, mot de passe trop court...
            st.error(message_erreur(reponse))
