# Point d'entrée de l'interface Streamlit LaborScope.
#
# Lancement (depuis le dossier frontend, avec l'API lancée dans un autre terminal) :
#     uv run streamlit run src/app.py
# Puis ouvrir le lien du port 8000 (sur Onyxia : Mes services > VSCode > Ouvrir)
#
# VERSION DE DÉMONSTRATION (étape 3) : elle sera remplacée par la navigation entre les pages.

import pandas as pd
import streamlit as st

from utils.api_client import api_client

# Réglages de l'onglet du navigateur : doit être la première commande Streamlit
st.set_page_config(page_title="LaborScope", page_icon="📊", layout="wide")

st.title("Bonjour LaborScope 👋")
st.write("Analyse interactive du marché du travail mondial (ILOSTAT).")

# --- Premier appel au backend : la liste des indicateurs ---------------------------------

st.subheader("Indicateurs disponibles")

reponse = api_client.get("/indicateurs")

if reponse["status_code"] == 200:
    indicateurs = reponse["data"]  # liste de dict, ex [{'code': ..., 'libelle': ...}, ...]
    if indicateurs:
        st.dataframe(pd.DataFrame(indicateurs), hide_index=True)
    else:
        st.info("Aucun indicateur en base : lancez l'import (python -m fetcher.charger_donnees).")
elif reponse["status_code"] == 0:  # backend injoignable
    st.error(reponse["data"])
else:  # le backend a répondu avec une erreur
    st.error(f"Erreur {reponse['status_code']} : {reponse['data']}")
