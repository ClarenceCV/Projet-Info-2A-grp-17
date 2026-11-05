# Page « Gestion des données » (administrateurs) : import ILOSTAT, modification et suppression d'observations.
# Endpoints utilisés : POST /admin/utilisateurs/import,
#                      GET /observations,
#                      PUT / DELETE /admin/utilisateurs/observations (corps JSON = la clé de l'observation)
# Backend : responsable A ; page : B (même structure que admin_utilisateurs.py et explorer.py)

import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_admin
from utils.selecteurs import choisir_classif1, choisir_indicateur, choisir_pays, choisir_sexe
from utils.session import message_erreur

exiger_admin()  # protège la page (c.f. utils/auth_guard.py)

# Les 6 colonnes qui identifient une observation (même ordre que CleObservationModel côté backend)
COLONNES_CLE = ["indicateur", "code_iso", "source", "periode", "sexe", "classif1"]
LIMITE = 1000  # nombre maximum d'observations affichées

st.title("Gestion des données")

# Message laissé par l'action précédente (import, modification, suppression), affiché après le st.rerun()
if "message_donnees" in st.session_state:
    st.success(st.session_state.pop("message_donnees"))  # pop : affiché une seule fois


def afficher_erreur(reponse: dict):
    """Affiche l'erreur d'une réponse de api_client (backend injoignable ou réponse en erreur)."""
    st.error(message_erreur(reponse) if reponse["status_code"] else reponse["data"])


# --- 1. Import depuis ILOSTAT ------------------------------------------------------------

st.subheader("Importer les données ILOSTAT")
st.write(
    "Télécharge à nouveau tous les indicateurs suivis depuis l'API ILOSTAT. "
    "Les observations existantes sont mises à jour, sans doublon."
)
st.warning("Les modifications manuelles faites ci-dessous seront écrasées par les valeurs ILOSTAT.")

confirme_import = st.checkbox("Je confirme vouloir relancer l'import")
if st.button("Forcer l'import", type="primary", disabled=not confirme_import):
    with st.spinner("Import en cours (cela peut prendre plusieurs minutes)..."):
        # timeout long : l'import télécharge chaque pays un par un (les 10 s par défaut ne suffisent pas)
        reponse = api_client.post("/admin/utilisateurs/import", timeout=900)
    if reponse["status_code"] == 200:
        st.cache_data.clear()  # les menus (pays, classif1...) sont en cache : on les relira
        nb = reponse["data"]["observations_enregistrees"]
        st.session_state["message_donnees"] = f"Import terminé : {nb} observations enregistrées."
        st.rerun()
    else:
        afficher_erreur(reponse)

st.divider()

# --- 2. Rechercher les observations à corriger ------------------------------------------

st.subheader("Modifier ou supprimer une observation")

colonne_gauche, colonne_droite = st.columns(2)
with colonne_gauche:
    indicateur = choisir_indicateur(cle="admin")
    pays = choisir_pays(cle="admin")
with colonne_droite:
    classif1 = choisir_classif1(indicateur, cle="admin")
    sexe = choisir_sexe(cle="admin")

if not (indicateur and pays and classif1):
    st.info("Choisissez un indicateur, au moins un pays et une modalité.")
    st.stop()

reponse = api_client.get(
    "/observations",
    params={"indicateur": indicateur, "pays": pays, "classif1": classif1, "sexe": sexe, "limite": LIMITE},
)
if reponse["status_code"] != 200:
    afficher_erreur(reponse)
    st.stop()

observations = pd.DataFrame(reponse["data"])
if observations.empty:
    st.info("Aucune observation pour ces filtres.")
    st.stop()
if len(observations) == LIMITE:
    st.caption(f"Seules les {LIMITE} premières observations sont affichées : affinez les filtres.")

# Tableau cliquable : on_select="rerun" relance la page quand une ligne est cochée.
# La clé change après chaque action (compteur) pour repartir d'un tableau sans ligne cochée.
st.write("Cochez la ligne à modifier ou à supprimer :")
version = st.session_state.get("version_tableau", 0)
tableau = st.dataframe(
    observations,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key=f"tableau_observations_{version}",
)

lignes_cochees = tableau.selection.rows  # liste des numéros de lignes cochées (0 ou 1 ici)
if not lignes_cochees:
    st.stop()

ligne = observations.iloc[lignes_cochees[0]]
cle = {colonne: ligne[colonne] for colonne in COLONNES_CLE}  # le corps JSON attendu par le backend
description = f"{ligne['nom_pays']}, {ligne['periode']}, {ligne['sexe']}, {ligne['classif1']}"


def apres_action(message: str):
    """Garde le message pour l'afficher après le rerun, et décoche la ligne (nouveau tableau)."""
    st.session_state["message_donnees"] = message
    st.session_state["version_tableau"] = version + 1
    st.rerun()


st.markdown(f"**Observation choisie :** {description} (source : {ligne['source']})")
colonne_modifier, colonne_supprimer = st.columns(2)

# --- 3. Modifier la valeur --------------------------------------------------------------

with colonne_modifier:
    nouvelle_valeur = st.number_input(
        f"Nouvelle valeur ({ligne['unite']})", value=float(ligne["valeur"]), format="%.3f"
    )
    if st.button("Modifier", type="primary"):
        reponse = api_client.put(
            "/admin/utilisateurs/observations",
            json=cle,                                   # la clé : dans le corps de la requête
            params={"nouvelle_valeur": nouvelle_valeur},  # la valeur : dans l'URL (?nouvelle_valeur=...)
        )
        if reponse["status_code"] == 200:
            apres_action(f"Observation modifiée ({description}) : {ligne['valeur']} → {nouvelle_valeur}.")
        else:
            afficher_erreur(reponse)

# --- 4. Supprimer -----------------------------------------------------------------------

with colonne_supprimer:
    confirme = st.checkbox("Je confirme la suppression de cette observation")
    if st.button("Supprimer", type="primary", disabled=not confirme, key="bouton_supprimer"):
        reponse = api_client.delete("/admin/utilisateurs/observations", json=cle)
        if reponse["status_code"] == 200:
            apres_action(f"Observation supprimée ({description}).")
        else:
            afficher_erreur(reponse)
