# Page « Se connecter » : formulaire pseudo + mot de passe.
# Endpoint utilisé : POST /login (via utils/session.py)
# Responsable : B

import streamlit as st

from utils.session import connecter

st.title("Se connecter")

# st.form : les champs ne déclenchent pas de réexécution, tout est envoyé d'un coup au clic sur le bouton
with st.form("formulaire_connexion"):
    pseudo = st.text_input("Pseudo")
    mot_de_passe = st.text_input("Mot de passe", type="password")  # caractères masqués
    envoye = st.form_submit_button("Se connecter", type="primary")

if envoye:
    if not pseudo or not mot_de_passe:
        st.error("Renseignez votre pseudo et votre mot de passe.")
    else:
        erreur = connecter(pseudo, mot_de_passe)
        if erreur:
            st.error(erreur)
        else:
            st.switch_page("pages/accueil.py")  # app.py reconstruit le menu selon le rôle

st.write("Pas encore de compte ?")
if st.button("Créer un compte"):
    st.switch_page("pages/creer_compte.py")
