# Page « Gestion des utilisateurs » (administrateurs) : liste, création, suppression des comptes.
# Endpoints utilisés : GET / POST /admin/utilisateurs, DELETE /admin/utilisateurs/{id}
# Responsable : B

import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_admin
from utils.session import message_erreur

exiger_admin()  # protège la page (c.f. utils/auth_guard.py)

st.title("Gestion des utilisateurs")

# Message laissé par l'action précédente (création, suppression), affiché après le st.rerun()
if "message_admin" in st.session_state:
    st.success(st.session_state.pop("message_admin"))  # pop : affiché une seule fois

# --- Liste des comptes (lue à chaque exécution : toujours à jour) --------------------------

reponse = api_client.get("/admin/utilisateurs")
if reponse["status_code"] != 200:
    st.error(message_erreur(reponse) if reponse["status_code"] else reponse["data"])
    st.stop()
utilisateurs = reponse["data"]  # liste de dict : id, pseudo, role, date_creation

st.subheader(f"Comptes ({len(utilisateurs)})")
st.dataframe(pd.DataFrame(utilisateurs), hide_index=True)

colonne_gauche, colonne_droite = st.columns(2)

# --- Créer un compte ----------------------------------------------------------------------

with colonne_gauche:
    st.subheader("Ajouter un compte")
    with st.form("formulaire_ajout", clear_on_submit=True):  # champs vidés après l'envoi
        pseudo = st.text_input("Pseudo")
        mot_de_passe = st.text_input("Mot de passe", type="password", help="8 caractères minimum")
        role = st.selectbox(
            "Rôle", ["utilisateur", "admin"],
            format_func=lambda r: "Administrateur" if r == "admin" else "Utilisateur",
        )
        ajouter = st.form_submit_button("Ajouter", type="primary")

    if ajouter:
        reponse = api_client.post(
            "/admin/utilisateurs", json={"pseudo": pseudo, "mot_de_passe": mot_de_passe, "role": role}
        )
        if reponse["status_code"] == 201:
            st.session_state["message_admin"] = f"Compte « {pseudo} » créé ({role})."
            st.rerun()  # relance la page : le tableau ci-dessus inclura le nouveau compte
        else:
            st.error(message_erreur(reponse) if reponse["status_code"] else reponse["data"])

# --- Supprimer un compte ------------------------------------------------------------------

with colonne_droite:
    st.subheader("Supprimer un compte")
    # on ne propose pas son propre compte (l'API le refuserait de toute façon)
    autres = [u for u in utilisateurs if u["pseudo"] != st.session_state["pseudo"]]
    if not autres:
        st.info("Aucun autre compte.")
    else:
        a_supprimer = st.selectbox(
            "Compte", autres, format_func=lambda u: f"{u['pseudo']} ({u['role']})"
        )
        confirme = st.checkbox(f"Je confirme la suppression de « {a_supprimer['pseudo']} »")
        if st.button("Supprimer", type="primary", disabled=not confirme, key="bouton_supprimer"):
            reponse = api_client.delete(f"/admin/utilisateurs/{a_supprimer['id']}")
            if reponse["status_code"] == 200:
                st.session_state["message_admin"] = f"Compte « {a_supprimer['pseudo']} » supprimé."
                st.rerun()
            else:
                st.error(message_erreur(reponse) if reponse["status_code"] else reponse["data"])
