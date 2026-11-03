# Page « Logs et historique » (administrateurs)
#   - Historique des actions des utilisateurs : GET /admin/journal   (responsable B)
#   - Logs techniques du backend : GET /admin/logs                   (responsable A, à faire)

import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_admin
from utils.session import message_erreur

exiger_admin()  # protège la page (c.f. utils/auth_guard.py)

st.title("Logs et historique")

onglet_historique, onglet_logs = st.tabs(["Historique des actions", "Logs techniques"])

# --- Historique des actions (B) -----------------------------------------------------------

# Mêmes mots-clés que ACTIONS dans backend/src/business_object/action_journal.py
ACTIONS = {
    None: "Toutes les actions",
    "connexion": "Connexion",
    "echec_connexion": "Échec de connexion",
    "deconnexion": "Déconnexion",
    "creation_compte": "Création de compte",
    "suppression_compte": "Suppression de compte",
    "import_donnees": "Import des données ILOSTAT",
    "modification_donnee": "Modification d'une donnée",
    "suppression_donnee": "Suppression d'une donnée",
}

with onglet_historique:
    colonne_action, colonne_pseudo, colonne_limite = st.columns([2, 2, 1])
    action = colonne_action.selectbox("Action", list(ACTIONS), format_func=lambda a: ACTIONS[a])
    pseudo = colonne_pseudo.text_input("Pseudo (début)", placeholder="ex : ad")
    limite = colonne_limite.number_input("Nombre max.", min_value=10, max_value=5000, value=200, step=50)

    # les paramètres à None sont ignorés par requests : pas de filtre envoyé
    reponse = api_client.get(
        "/admin/journal", params={"action": action, "pseudo": pseudo or None, "limite": limite}
    )

    if reponse["status_code"] != 200:
        st.error(message_erreur(reponse) if reponse["status_code"] else reponse["data"])
    elif not reponse["data"]:
        st.info("Aucune action ne correspond à ces filtres.")
    else:
        df = pd.DataFrame(reponse["data"])

        # quelques chiffres sur les actions affichées
        nb = df["action"].value_counts()
        a, b, c = st.columns(3)
        a.metric("Actions affichées", len(df))
        b.metric("Connexions", int(nb.get("connexion", 0)))
        c.metric("Échecs de connexion", int(nb.get("echec_connexion", 0)))

        # mise en forme du tableau : colonnes lisibles, date sans les microsecondes
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y %H:%M:%S")
        df["pseudo"] = df["pseudo"].fillna("—")
        st.dataframe(
            df[["date", "pseudo", "libelle_action", "detail"]].rename(
                columns={"date": "Date", "pseudo": "Pseudo", "libelle_action": "Action", "detail": "Détail"}
            ),
            hide_index=True,
            width="stretch",  # toute la largeur de la page
        )

# --- Logs techniques (A) ------------------------------------------------------------------

with onglet_logs:
    st.info("🚧 En construction : responsable A (endpoint prévu : GET /admin/logs).")
