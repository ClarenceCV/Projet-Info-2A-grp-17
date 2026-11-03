# Page « Comparaison entre pays (F4) » : classement d'un indicateur entre pays, pays les plus hauts / plus bas.
# Endpoint utilisé : GET /analyses/comparaison-pays
# Responsable : D (modèle suivi : pages/explorer.py → sélecteurs → api_client → affichage)

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_connexion
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_pays, choisir_sexe

exiger_connexion()  # protège la page (c.f. utils/auth_guard.py)

st.title("Comparaison entre pays (F4)")
st.write("Comparez un indicateur entre plusieurs pays, à la période la plus récente disponible de chaque pays.")

# 1. Recueillir les choix : les menus, côte à côte sur 2 colonnes
colonne_gauche, colonne_droite = st.columns(2)
with colonne_gauche:
    indicateur = choisir_indicateur()
    pays = choisir_pays(defaut=["FRA", "DEU", "ESP", "ITA"])
with colonne_droite:
    classif1 = choisir_classif1(indicateur)
    sexe = choisir_sexe()
    top = st.number_input("Nombre de pays « plus hauts » / « plus bas »", min_value=1, max_value=50, value=3)

if not (indicateur and pays and classif1):
    st.info("Choisissez un indicateur, au moins un pays et une modalité.")
    st.stop()  # arrête l'exécution de la page ici (rien ne s'affiche en dessous)

# 2. Appeler l'endpoint
reponse = api_client.get(
    "/analyses/comparaison-pays",
    params={"indicateur": indicateur, "pays": pays, "classif1": classif1, "sexe": sexe, "top": top},
)

if reponse["status_code"] == 0:  # backend injoignable
    st.error(reponse["data"])
    st.stop()
if reponse["status_code"] != 200:  # le backend a répondu avec une erreur
    st.error(f"Erreur {reponse['status_code']} : {reponse['data']}")
    st.stop()

donnees = reponse["data"]
classement = pd.DataFrame(donnees["classement"])
plus_hauts = pd.DataFrame(donnees["plus_hauts"])
plus_bas = pd.DataFrame(donnees["plus_bas"])

if classement.empty:
    st.warning("Aucune donnée pour ces choix.")
    st.stop()

# 3. Présenter le résultat

# Prévenir si les pays ne sont pas tous comparés à la même période (choix (b) : dernière période de chaque pays)
st.write(f"Période la plus récente : **{donnees['periode_reference']}**")
if classement["periode"].nunique() > 1:
    st.warning("Attention : les pays n'ont pas tous la même dernière période (voir la colonne « periode »).")

# Couleur de chaque barre : plus hauts, plus bas, ou autres
classement["groupe"] = "Autres"
classement.loc[classement["code_iso"].isin(plus_bas["code_iso"]), "groupe"] = "Plus bas"
classement.loc[classement["code_iso"].isin(plus_hauts["code_iso"]), "groupe"] = "Plus hauts"

# Diagramme en barres horizontales (le pays le plus haut en haut)
fig = px.bar(
    classement,
    x="valeur",
    y="nom_pays",
    orientation="h",
    color="groupe",
    color_discrete_map={"Plus hauts": "green", "Plus bas": "red", "Autres": "grey"},
    hover_data=["periode", "unite"],
    labels={"valeur": f"Valeur ({classement['unite'].iloc[0]})", "nom_pays": "Pays", "groupe": ""},
)
fig.update_yaxes(categoryorder="total ascending")
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
