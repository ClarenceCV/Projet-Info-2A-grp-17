# Page « Carte du monde (FO2) » : EN CONSTRUCTION
# Responsable : D (voir sa fiche dans doc/taches/)
# Endpoint prévu : GET /analyses/comparaison-pays (tous les pays)
#
# Modèle à suivre : pages/explorer.py (sélecteurs → api_client → affichage)

import streamlit as st

from utils.auth_guard import exiger_connexion

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Carte du monde (FO2)")
st.info("🚧 Page en construction : responsable D.")
