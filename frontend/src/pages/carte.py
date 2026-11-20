"""Page « Carte du monde (FO2) » : un indicateur sur une carte du monde, couleur selon la valeur de
chaque pays.
Endpoint utilisé : GET /analyses/comparaison-pays (sans pays → tous les pays de la base)
Responsable : D (pas de nouvel endpoint : c'est la comparaison F4 de tous les pays, affichée sur une
carte)
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_connexion
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_sexe
from utils.session import donnees_ou_arret

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Carte du monde (FO2)")
st.write(
    "Visualisez un indicateur sur une carte du monde, "
    "à la période la plus récente disponible de chaque pays."
)

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

# 2. Appeler l'endpoint de la comparaison entre pays (F4), sans pays (sans période : la dernière)
parametres = {"indicateur": indicateur, "classif1": classif1, "sexe": sexe}
reponse = api_client.get("/analyses/comparaison-pays", params=parametres)

donnees = donnees_ou_arret(reponse)  # en cas d'erreur : message affiché et page arrêtée

# Choix de la période, avec une case à cocher (comme la page comparaison_pays.py) :
# - cochée : la dernière période commune à tous les pays (pour l'indicateur choisi) ;
# - décochée : la période choisie dans le menu (par défaut la dernière disponible de chaque pays ;
#   si un pays n'a pas la période choisie, on prend sa dernière période avant celle-ci)
periode_commune_cochee = st.checkbox("Utiliser la dernière période commune à tous les pays")

if periode_commune_cochee:
    if donnees["periode_commune"] is None:
        st.warning("Aucune période n'est commune à tous les pays de la carte : "
                   "décochez la case pour choisir une période.")
        st.stop()
    choix_periode = donnees["periode_commune"]  # ex : '2024Q4'
else:
    # la liste vient de la première réponse, de la plus récente à la plus ancienne
    liste_periodes = ["Dernière disponible"] + donnees["periodes_disponibles"][::-1]
    choix_periode = st.selectbox("Période", liste_periodes)

if choix_periode != "Dernière disponible":
    # on rappelle l'endpoint avec la période choisie
    parametres["periode"] = choix_periode
    reponse = api_client.get("/analyses/comparaison-pays", params=parametres)
    donnees = donnees_ou_arret(reponse)

df = pd.DataFrame(donnees["classement"])

if df.empty:
    st.warning("Aucune donnée pour ces choix.")
    st.stop()

# 3. Présenter le résultat
st.write(
    f"Période la plus récente : **{donnees['periode_reference']}** "
    f"({len(df)} pays avec des données)"
)
if df["periode"].nunique() > 1:
    st.warning("Attention : les pays n'ont pas tous la même période (voir le tableau).")

# Carte choroplèthe : code_iso = code ISO à 3 lettres, Plotly le reconnaît
fig = px.choropleth(
    df,
    locations="code_iso",
    color="valeur",
    hover_name="nom_pays",
    hover_data=["periode", "unite"],
    color_continuous_scale="Blues",  # une seule couleur : clair = petite valeur, foncé = grande valeur
)
st.plotly_chart(fig)
st.caption("Les pays en blanc n'ont pas de données dans la base.")

# Le tableau des valeurs affichées sur la carte
st.dataframe(df[["rang", "nom_pays", "periode", "valeur", "unite"]], hide_index=True)
