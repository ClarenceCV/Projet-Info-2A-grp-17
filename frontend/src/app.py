# Point d'entrée de l'interface Streamlit LaborScope.
#
# Lancement (depuis le dossier frontend) :
#     uv run streamlit run src/app.py
# Puis ouvrir le lien du port 8000 (sur Onyxia : Mes services > VSCode > Ouvrir)
#
# VERSION DE DÉMONSTRATION (étape 2) : elle sera remplacée par la navigation entre les pages.

import streamlit as st

# Réglages de l'onglet du navigateur : doit être la première commande Streamlit
st.set_page_config(page_title="LaborScope", page_icon="📊", layout="wide")

st.title("Bonjour LaborScope 👋")
st.write("Analyse interactive du marché du travail mondial (ILOSTAT).")

# --- Démonstration : Streamlit réexécute TOUT ce fichier à chaque clic -------------------

st.subheader("Démonstration du modèle d'exécution")

# 1. Variable Python classique : remise à 0 à chaque réexécution
compteur_python = 0
if st.button("Ajouter 1 (variable Python)"):
    compteur_python += 1
st.write(f"Variable Python : {compteur_python}  ← reste bloquée à 0 ou 1")

# 2. st.session_state : conservé d'une réexécution à l'autre (tant que l'onglet reste ouvert)
if "compteur" not in st.session_state:  # seulement à la toute première exécution
    st.session_state["compteur"] = 0
if st.button("Ajouter 1 (session_state)"):
    st.session_state["compteur"] += 1
st.write(f"st.session_state : {st.session_state['compteur']}  ← augmente vraiment")
