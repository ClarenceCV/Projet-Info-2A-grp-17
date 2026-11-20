# Page « Logs et historique » (administrateurs)
#   - Historique des actions des utilisateurs : GET /admin/journal   (responsable B)
#   - Logs techniques du backend : GET /admin/logs                   (responsable A)

import re

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

# Format d'une ligne du fichier de logs (c.f. formatter "detailed" de backend/logging_config.yml) :
#     2026-11-20 12:45:55,622 - INFO - [_client.py:1025] - HTTP Request: GET ...
FORMAT_LIGNE = re.compile(r"^(\S+ \S+) - (\w+) - \[(.*?)\] - (.*)$")
NIVEAUX = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def decouper_logs(lignes: list[str]) -> pd.DataFrame:
    """
    Transforme les lignes brutes du fichier de logs en tableau (date, niveau, source, message).
    Une ligne qui ne suit pas le format (ex : les lignes d'une erreur Python, le « traceback »)
    est rattachée au message de la ligne précédente.
    """
    entrees = []
    for ligne in lignes:
        ligne = ligne.rstrip("\n")
        morceaux = FORMAT_LIGNE.match(ligne)
        if morceaux:
            date, niveau, source, message = morceaux.groups()
            entrees.append({"Date": date.split(",")[0], "Niveau": niveau, "Source": source, "Message": message})
        elif entrees:
            entrees[-1]["Message"] += "\n" + ligne
    return pd.DataFrame(entrees, columns=["Date", "Niveau", "Source", "Message"])


with onglet_logs:
    colonne_niveaux, colonne_recherche, colonne_lignes = st.columns([2, 2, 1])
    # DEBUG est exclu par défaut : très bavard (détails internes des bibliothèques)
    niveaux = colonne_niveaux.multiselect("Niveaux", NIVEAUX, default=["INFO", "WARNING", "ERROR", "CRITICAL"])
    recherche = colonne_recherche.text_input("Rechercher dans les messages", placeholder="ex : rapport")
    nb_lignes = colonne_lignes.number_input("Lignes lues", min_value=50, max_value=5000, value=500, step=50)
    st.button("Actualiser", icon=":material/refresh:")  # un clic relance la page, donc relit les logs

    reponse = api_client.get("/admin/logs", params={"lignes": nb_lignes})

    if reponse["status_code"] == 404:
        st.info("Aucun fichier de logs pour l'instant : il est créé au premier démarrage de l'API.")
    elif reponse["status_code"] != 200:
        st.error(message_erreur(reponse) if reponse["status_code"] else reponse["data"])
    else:
        lignes_brutes = reponse["data"]["logs"]
        df_logs = decouper_logs(lignes_brutes)

        # chiffres sur les lignes lues (avant filtres)
        a, b, c = st.columns(3)
        a.metric("Entrées lues", len(df_logs))
        b.metric("Avertissements", int((df_logs["Niveau"] == "WARNING").sum()))
        c.metric("Erreurs", int(df_logs["Niveau"].isin(["ERROR", "CRITICAL"]).sum()))

        # filtres, puis les plus récentes en haut
        df_logs = df_logs[df_logs["Niveau"].isin(niveaux)]
        if recherche:
            df_logs = df_logs[df_logs["Message"].str.contains(recherche, case=False, regex=False)]

        if df_logs.empty:
            st.info("Aucune entrée ne correspond à ces filtres.")
        else:
            st.dataframe(df_logs.iloc[::-1], hide_index=True, width="stretch")

        st.download_button(
            "Télécharger les lignes lues (.log)",
            data="".join(lignes_brutes),
            file_name="laborscope.log",
            mime="text/plain",
            icon=":material/download:",
        )
