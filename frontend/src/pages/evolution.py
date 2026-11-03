# Page « Évolution d'un indicateur (F3) » : EN CONSTRUCTION
# Responsable : C (voir sa fiche dans doc/taches/)
# Endpoint prévu : GET /analyses/evolution
#
# Modèle à suivre : pages/explorer.py (sélecteurs → api_client → affichage)

# Page Streamlit : évolution d'un indicateur sur les N derniers trimestres (F3).
# Utilise les sélecteurs (utils/selecteurs.py) et le client API (utils/api_client.py) de B.
# ####Adapter les noms de fonctions importées à ceux réellement présents dans le code de B.

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.api_client import get
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_pays, choisir_sexe

st.title("Évolution d'un indicateur-Fonctionnalité F3")

indicateur = choisir_indicateur()
pays = choisir_pays(multiple=True)
classif1 = choisir_classif1(indicateur)
sexe = choisir_sexe()
n = st.slider("Nombre de trimestres", 2, 20, 8)

if not pays:
    st.info("Sélectionnez au moins un pays.")
    st.stop()

donnees = get(
    "/analyses/evolution",
    {"indicateur": indicateur, "pays": pays, "classif1": classif1, "sexe": sexe, "n_periodes": n},
)
df = pd.DataFrame(donnees)

if df.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

unite = df["unite"].iloc[0]

# 1. évolution de la valeur : une courbe par pays
st.subheader("Évolution de la valeur")
fig = px.line(
    df, x="periode", y="valeur", color="nom_pays", markers=True,
    labels={"periode": "Période", "valeur": f"Valeur ({unite})", "nom_pays": "Pays"},
)
st.plotly_chart(fig, use_container_width=True)

# 2. variation par rapport à la période précédente : barres groupées par pays
st.subheader("Variation par rapport à la période précédente")
fig_var = px.bar(
    df.dropna(subset=["variation_abs"]), x="periode", y="variation_abs", color="nom_pays",
    barmode="group",
    labels={"periode": "Période", "variation_abs": f"Variation ({unite})", "nom_pays": "Pays"},
)
st.plotly_chart(fig_var, use_container_width=True)

# 3. tableau détaillé
st.subheader("Détail")
tableau = df.rename(columns={
    "code_iso": "Code", "nom_pays": "Pays", "periode": "Période", "valeur": f"Valeur ({unite})",
    "variation_abs": "Variation abs.", "variation_pct": "Variation (%)",
}).drop(columns=["unite"])
st.dataframe(tableau, use_container_width=True, hide_index=True)
