"""Page « Comparaison entre pays (F4) » : classement d'un indicateur entre pays, pays les plus hauts
/ plus bas.
Endpoint utilisé : GET /analyses/comparaison-pays
Responsable : D (modèle suivi : pages/explorer.py → sélecteurs → api_client → affichage)
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_connexion
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_pays, choisir_sexe
from utils.session import donnees_ou_arret

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Comparaison entre pays (F4)")
st.write(
    "Comparez un indicateur entre plusieurs pays, "
    "à la période la plus récente disponible de chaque pays."
)

# 1. Recueillir les choix : les menus, côte à côte sur 2 colonnes
colonne_gauche, colonne_droite = st.columns(2)
with colonne_gauche:
    indicateur = choisir_indicateur()
    pays = choisir_pays(defaut=["FRA", "DEU", "ESP", "ITA"])
with colonne_droite:
    classif1 = choisir_classif1(indicateur)
    sexe = choisir_sexe()
    top = st.number_input(
        "Nombre de pays « plus hauts » / « plus bas »", min_value=1, max_value=50, value=3
    )
    colorer_extremes = st.checkbox("Mettre en couleur les plus hauts / plus bas", value=True)

if not (indicateur and pays and classif1):
    st.info("Choisissez un indicateur, au moins un pays et une modalité.")
    st.stop()  # arrête l'exécution de la page ici (rien ne s'affiche en dessous)

# 2. Appeler l'endpoint (sans période : dernière période de chaque pays)
parametres = {"indicateur": indicateur, "pays": pays, "classif1": classif1,
              "sexe": sexe, "top": top}
reponse = api_client.get("/analyses/comparaison-pays", params=parametres)

donnees = donnees_ou_arret(reponse)  # en cas d'erreur : message affiché et page arrêtée

# Choix de la période, avec une case à cocher :
# - cochée : la dernière période commune à tous les pays (pour l'indicateur choisi) ;
# - décochée : la période choisie dans le menu (par défaut la dernière disponible de chaque pays ;
#   si un pays n'a pas la période choisie, on prend sa dernière période avant celle-ci)
periode_commune_cochee = st.checkbox("Utiliser la dernière période commune à tous les pays")

if periode_commune_cochee:
    if donnees["periode_commune"] is None:
        st.warning("Aucune période n'est commune à tous les pays choisis : "
                   "retirez des pays ou décochez la case pour choisir une période.")
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
classement = pd.DataFrame(donnees["classement"])
plus_hauts = pd.DataFrame(donnees["plus_hauts"])
plus_bas = pd.DataFrame(donnees["plus_bas"])

if classement.empty:
    st.warning("Aucune donnée pour ces choix.")
    st.stop()

# 3. Présenter le résultat

# Prévenir si les pays ne sont pas tous comparés à la même période (choix (b) : dernière période de
# chaque pays)
st.write(f"Période la plus récente : **{donnees['periode_reference']}**")
if classement["periode"].nunique() > 1:
    st.warning(
        "Attention : les pays n'ont pas tous la même période "
        "(voir la colonne « periode »)."
    )

# Couleur de chaque barre : plus hauts, plus bas, ou autres (si la case est décochée : tout en gris)
classement["groupe"] = "Autres"
if colorer_extremes:
    classement.loc[classement["code_iso"].isin(plus_bas["code_iso"]), "groupe"] = "Plus bas"
    classement.loc[classement["code_iso"].isin(plus_hauts["code_iso"]), "groupe"] = "Plus hauts"

# Diagramme en barres horizontales (le pays le plus haut en haut)
fig = px.bar(
    classement,
    x="valeur",
    y="nom_pays",
    orientation="h",
    color="groupe",
    # mêmes bleus que l'échelle "Blues" de la carte (carte.py)
    color_discrete_map={
        "Plus hauts": "rgb(8,48,107)",  # bleu foncé
        "Plus bas": "rgb(158,202,225)",  # bleu clair
        "Autres": "rgb(200,200,200)",  # gris doux
    },
    hover_data=["periode", "unite"],
    labels={"valeur": f"Valeur ({classement['unite'].iloc[0]})", "nom_pays": "Pays", "groupe": ""},
)
fig.update_yaxes(categoryorder="total ascending")
fig.update_layout(showlegend=colorer_extremes)  # pas de légende si toutes les barres sont grises
# hauteur selon le nombre de pays (25 pixels par barre, 400 au minimum) : tous les noms restent lisibles
fig.update_layout(height=max(400, 25 * len(classement)))
st.plotly_chart(fig)

# Encadrés : valeurs les plus hautes / les plus basses
colonnes_affichees = ["rang", "nom_pays", "periode", "valeur", "unite"]
colonne_gauche, colonne_droite = st.columns(2)
with colonne_gauche:
    st.subheader("Valeurs les plus hautes")
    st.dataframe(plus_hauts[colonnes_affichees], hide_index=True)
with colonne_droite:
    st.subheader("Valeurs les plus basses")
    st.dataframe(plus_bas[colonnes_affichees], hide_index=True)

# Le classement complet
st.subheader("Classement complet")
st.dataframe(classement[colonnes_affichees], hide_index=True)
