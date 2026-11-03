# Page « Carte du monde (FO2) » : un indicateur sur une carte du monde, couleur selon la valeur de chaque pays.
# Endpoint utilisé : GET /analyses/comparaison-pays (sans pays → tous les pays de la base)
# Responsable : D (pas de nouvel endpoint : c'est la comparaison F4 de tous les pays, affichée sur une carte)

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_connexion
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_sexe

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Carte du monde (FO2)")
st.write("Visualisez un indicateur sur une carte du monde, à la période la plus récente disponible de chaque pays.")

# 1. Recueillir les choix (pas de choix de pays : on affiche tous les pays de la base)
colonne_gauche, colonne_droite = st.columns(2)
with colonne_gauche:
    indicateur = choisir_indicateur()
    sexe = choisir_sexe()
with colonne_droite:
    classif1 = choisir_classif1(indicateur)

if not (indicateur and classif1):
    st.info("Choisissez un indicateur et une modalité.")
    st.stop()  # arrête l'exécution de la page ici (rien ne s'affiche en dessous)

# 2. Appeler l'endpoint de la comparaison entre pays (F4), sans pays
reponse = api_client.get(
    "/analyses/comparaison-pays",
    params={"indicateur": indicateur, "classif1": classif1, "sexe": sexe},
)

if reponse["status_code"] == 0:  # backend injoignable
    st.error(reponse["data"])
    st.stop()
if reponse["status_code"] != 200:  # le backend a répondu avec une erreur
    st.error(f"Erreur {reponse['status_code']} : {reponse['data']}")
    st.stop()

donnees = reponse["data"]
df = pd.DataFrame(donnees["classement"])

if df.empty:
    st.warning("Aucune donnée pour ces choix.")
    st.stop()

# 3. Présenter le résultat
st.write(f"Période la plus récente : **{donnees['periode_reference']}** ({len(df)} pays avec des données)")
if df["periode"].nunique() > 1:
    st.warning("Attention : les pays n'ont pas tous la même dernière période (voir le tableau).")

# Carte choroplèthe : code_iso = code ISO à 3 lettres, Plotly le reconnaît
fig = px.choropleth(
    df,
    locations="code_iso",
    color="valeur",
    hover_name="nom_pays",
    hover_data=["periode", "unite"],
    color_continuous_scale="Viridis",
)
st.plotly_chart(fig)
st.caption("Les pays en blanc n'ont pas de données dans la base.")

# Le tableau des valeurs affichées sur la carte
st.dataframe(df[["rang", "nom_pays", "periode", "valeur", "unite"]], hide_index=True)
