# Page d'accueil : présentation de l'application, visible par tout le monde.
# Responsable : B

import streamlit as st

st.title("📊 LaborScope")
st.subheader("Analyse interactive du marché du travail mondial")

st.write(
    "LaborScope s'appuie sur les données ouvertes de l'Organisation Internationale du Travail "
    "(ILOSTAT) pour suivre l'évolution de l'emploi par pays, sexe, tranche d'âge ou profession, "
    "et comparer les marchés du travail entre pays."
)

role = st.session_state.get("role")

if role is None:
    st.info("Connectez-vous ou créez un compte pour accéder aux analyses.")
    colonne_gauche, colonne_droite = st.columns(2)
    # st.switch_page : aller directement à une autre page (elle doit faire partie du menu)
    if colonne_gauche.button("Se connecter", type="primary", width="stretch"):
        st.switch_page("pages/connexion.py")
    if colonne_droite.button("Créer un compte", width="stretch"):
        st.switch_page("pages/creer_compte.py")
else:
    st.success(f"Bonjour {st.session_state['pseudo']} ! Choisissez une analyse dans le menu à gauche.")
