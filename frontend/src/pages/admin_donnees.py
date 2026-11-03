# Page « Gestion des données » : EN CONSTRUCTION
# Responsable : A (voir sa fiche dans doc/taches/)
# Endpoint prévu : POST /admin/import, PUT / DELETE /admin/observations
#
# Modèle à suivre : pages/explorer.py (sélecteurs → api_client → affichage)

import streamlit as st

from utils.auth_guard import exiger_admin

exiger_admin()  # protège la page (c.f. utils/auth_guard.py)

st.title("Gestion des données")
st.info("🚧 Page en construction : responsable A.")
