# Page « Rapport PDF (FO3) » : EN CONSTRUCTION
# Responsable : E (voir sa fiche dans doc/taches/)
# Endpoint prévu : GET /rapport
#
# Modèle à suivre : pages/explorer.py (sélecteurs → api_client → affichage)

import streamlit as st

from utils.auth_guard import exiger_connexion

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Rapport PDF (FO3)")
st.info("🚧 Page en construction : responsable E.")
