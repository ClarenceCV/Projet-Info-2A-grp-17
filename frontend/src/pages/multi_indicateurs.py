# Page « Comparaison multi-indicateurs (F5) » : EN CONSTRUCTION
# Responsable : E (voir sa fiche dans doc/taches/)
# Endpoint prévu : POST /analyses/multi-indicateurs
#
# Modèle à suivre : pages/explorer.py (sélecteurs → api_client → affichage)

import streamlit as st

from utils.auth_guard import exiger_connexion

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Comparaison multi-indicateurs (F5)")
st.info("🚧 Page en construction : responsable E.")
