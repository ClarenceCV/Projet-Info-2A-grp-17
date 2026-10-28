# Point d'entrée de l'interface Streamlit LaborScope : construit le menu selon le rôle de l'utilisateur
# (c.f. diagrammes d'activité du rapport : visiteur → connexion → menu utilisateur / menu administrateur).
#
# Lancement (depuis le dossier frontend, avec l'API lancée dans un autre terminal) :
#     uv run streamlit run src/app.py
# Puis ouvrir le lien du port 8000 (sur Onyxia : Mes services > VSCode > Ouvrir)
#
# Ce fichier est exécuté à CHAQUE clic, puis il exécute la page choisie (pg.run()).
# Pour ajouter une page : créer le fichier dans pages/ puis l'ajouter dans la bonne liste ci-dessous.

import streamlit as st

# Réglages de l'onglet du navigateur : doit être la première commande Streamlit (une seule fois, ici)
st.set_page_config(page_title="LaborScope", page_icon="📊", layout="wide")

# --- Les pages (fichier, titre dans le menu, icône) -------------------------------------
# Icônes : https://fonts.google.com/icons (écrire :material/nom_de_l_icone:)

accueil = st.Page("pages/accueil.py", title="Accueil", icon=":material/home:", default=True)

pages_visiteur = [
    st.Page("pages/connexion.py", title="Se connecter", icon=":material/login:"),
    st.Page("pages/creer_compte.py", title="Créer un compte", icon=":material/person_add:"),
]

pages_analyses = [
    st.Page("pages/explorer.py", title="Explorer les données", icon=":material/table:"),
    st.Page("pages/evolution.py", title="Évolution (F3)", icon=":material/show_chart:"),
    st.Page("pages/comparaison_pays.py", title="Comparaison pays (F4)", icon=":material/bar_chart:"),
    st.Page("pages/carte.py", title="Carte du monde (FO2)", icon=":material/public:"),
    st.Page("pages/multi_indicateurs.py", title="Multi-indicateurs (F5)", icon=":material/stacked_line_chart:"),
    st.Page("pages/rapport.py", title="Rapport PDF (FO3)", icon=":material/picture_as_pdf:"),
]

pages_admin = [
    st.Page("pages/admin_utilisateurs.py", title="Utilisateurs", icon=":material/group:"),
    st.Page("pages/admin_donnees.py", title="Données", icon=":material/database:"),
    st.Page("pages/admin_logs.py", title="Logs et historique", icon=":material/history:"),
]

# --- TEMPORAIRE (jusqu'à la page de connexion) : simuler un rôle pour tester les menus ----

with st.sidebar.expander("🛠️ Simuler un rôle (développement)"):
    role_simule = st.radio(
        "Rôle", options=["visiteur", "utilisateur", "admin"], key="role_simule", horizontal=True
    )
st.session_state["role"] = None if role_simule == "visiteur" else role_simule

# --- Le menu, selon le rôle ----------------------------------------------------------------

role = st.session_state.get("role")  # None (pas connecté), 'utilisateur' ou 'admin'

if role is None:
    menu = {"": [accueil] + pages_visiteur}
elif role == "utilisateur":
    menu = {"": [accueil], "Analyses": pages_analyses}
else:  # admin : tout ce que voit un utilisateur, plus l'administration
    menu = {"": [accueil], "Analyses": pages_analyses, "Administration": pages_admin}

pg = st.navigation(menu)  # dessine le menu latéral et renvoie la page choisie

# --- Bas du menu latéral : qui est connecté + déconnexion ---------------------------------

def se_deconnecter():
    """
    Oublie l'utilisateur connecté (la vraie déconnexion côté API arrivera avec la page de connexion).
    Appelée par le bouton (on_click) AVANT la réexécution du script : le menu sera celui du visiteur.
    """
    for cle in ("token", "pseudo", "role"):
        st.session_state.pop(cle, None)
    st.session_state["role_simule"] = "visiteur"  # TEMPORAIRE


if role is not None:
    st.sidebar.caption(f"Connecté en tant que **{role}**")
    st.sidebar.button("Se déconnecter", icon=":material/logout:", on_click=se_deconnecter)

pg.run()  # exécute le fichier de la page choisie
