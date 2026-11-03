# Page « Évolution d'un indicateur (F3) » : EN CONSTRUCTION
# Responsable : C (voir sa fiche dans doc/taches/)
# Endpoint prévu : GET /analyses/evolution
#
# Modèle à suivre : pages/explorer.py (sélecteurs → api_client → affichage)

import streamlit as st

from utils.auth_guard import exiger_connexion

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Évolution d'un indicateur (F3)")
st.info("🚧 Page en construction : responsable C.")
