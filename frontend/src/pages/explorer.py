"""Page « Explorer les données » : rechercher des observations brutes avec les sélecteurs communs.
Endpoint utilisé : GET /observations
Responsable : B (sert aussi d'exemple pour les autres pages : sélecteurs → api_client → affichage)
"""

import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_connexion
from utils.selecteurs import choisir_filtres
from utils.session import donnees_ou_arret

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Explorer les données")
st.write("Consultez les observations ILOSTAT enregistrées dans la base.")

# 1. Recueillir les choix : les 4 menus, côte à côte sur 2 colonnes (la page s'arrête si un
#    choix manque)
filtres = choisir_filtres()

# 2. Appeler l'endpoint (en cas d'erreur : message affiché et page arrêtée)
observations = donnees_ou_arret(api_client.get("/observations", params=filtres))

# 3. Présenter le résultat
st.dataframe(pd.DataFrame(observations), hide_index=True)
