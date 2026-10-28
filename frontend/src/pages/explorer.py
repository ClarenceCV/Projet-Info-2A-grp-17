# Page « Explorer les données » : rechercher des observations brutes avec les sélecteurs communs.
# Endpoint utilisé : GET /observations
# Responsable : B (sert aussi d'exemple pour les autres pages : sélecteurs → api_client → affichage)

import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_pays, choisir_sexe

st.title("Explorer les données")
st.write("Consultez les observations ILOSTAT enregistrées dans la base.")

# 1. Recueillir les choix : les menus, côte à côte sur 2 colonnes
colonne_gauche, colonne_droite = st.columns(2)
with colonne_gauche:
    indicateur = choisir_indicateur()
    pays = choisir_pays()
with colonne_droite:
    classif1 = choisir_classif1(indicateur)
    sexe = choisir_sexe()

if not (indicateur and pays and classif1):
    st.info("Choisissez un indicateur, au moins un pays et une modalité.")
    st.stop()  # arrête l'exécution de la page ici (rien ne s'affiche en dessous)

# 2. Appeler l'endpoint
reponse = api_client.get(
    "/observations",
    params={"indicateur": indicateur, "pays": pays, "classif1": classif1, "sexe": sexe},
)

# 3. Présenter le résultat
if reponse["status_code"] == 200:
    st.dataframe(pd.DataFrame(reponse["data"]), hide_index=True)
elif reponse["status_code"] == 0:  # backend injoignable
    st.error(reponse["data"])
else:  # le backend a répondu avec une erreur
    st.error(f"Erreur {reponse['status_code']} : {reponse['data']}")
