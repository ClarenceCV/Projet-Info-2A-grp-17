# Point d'entrée de l'interface Streamlit LaborScope.
#
# Lancement (depuis le dossier frontend, avec l'API lancée dans un autre terminal) :
#     uv run streamlit run src/app.py
# Puis ouvrir le lien du port 8000 (sur Onyxia : Mes services > VSCode > Ouvrir)
#
# VERSION DE DÉMONSTRATION (étape 4) : elle sera remplacée par la navigation entre les pages.

import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_pays, choisir_sexe

# Réglages de l'onglet du navigateur : doit être la première commande Streamlit
st.set_page_config(page_title="LaborScope", page_icon="📊", layout="wide")

st.title("Bonjour LaborScope 👋")
st.write("Analyse interactive du marché du travail mondial (ILOSTAT).")

# --- Démonstration des sélecteurs communs : choisir puis afficher des observations -------

st.subheader("Rechercher des observations")

# les menus, côte à côte sur 2 colonnes
colonne_gauche, colonne_droite = st.columns(2)
with colonne_gauche:
    indicateur = choisir_indicateur()
    pays = choisir_pays()
with colonne_droite:
    classif1 = choisir_classif1(indicateur)
    sexe = choisir_sexe()

if indicateur and pays and classif1:
    reponse = api_client.get(
        "/observations",
        params={"indicateur": indicateur, "pays": pays, "classif1": classif1, "sexe": sexe},
    )
    if reponse["status_code"] == 200:
        st.dataframe(pd.DataFrame(reponse["data"]), hide_index=True)
    elif reponse["status_code"] == 0:  # backend injoignable
        st.error(reponse["data"])
    else:  # le backend a répondu avec une erreur
        st.error(f"Erreur {reponse['status_code']} : {reponse['data']}")
else:
    st.info("Choisissez un indicateur, au moins un pays et une modalité.")
