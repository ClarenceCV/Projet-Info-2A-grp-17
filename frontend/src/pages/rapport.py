"""Page Streamlit - Rapport PDF (FO3).

Selecteurs -> api_client -> Telechargement direct du PDF.
"""

import streamlit as st
from utils.api_client import api_client
from utils.auth_guard import exiger_connexion

# Protege l'acces a la page (redirection vers /login si non connecte)
exiger_connexion()

st.title("Rapport PDF (FO3)")
st.markdown(
    "Generez et telechargez une synthese d'analyse au format PDF combinant "
    "evolutions temporelles, comparaisons entre pays et conclusions statistiques automatiques."
)

# ------------------------------------------------------------------------------
# 1. Chargement des metadonnees pour les selecteurs
# ------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def charger_filtres() -> tuple[list[dict], list[dict]]:
    """Recupere la liste des indicateurs et des pays via l'API client."""
    res_ind = api_client.get("/indicateurs")
    res_pays = api_client.get("/pays")

    indicateurs = res_ind["data"] if res_ind.get("status_code") == 200 and isinstance(res_ind.get("data"), list) else []
    pays = res_pays["data"] if res_pays.get("status_code") == 200 and isinstance(res_pays.get("data"), list) else []
    return indicateurs, pays


indicateurs_dispo, pays_dispo = charger_filtres()

# Dictionnaire pour formater le menu deroulant des indicateurs
dict_indicateurs = (
    {
        ind.get("code", ind.get("code_indicateur")): ind.get("libelle", ind.get("code"))
        for ind in indicateurs_dispo
    }
    if indicateurs_dispo
    else {"EMP_5EMP_SEX_OC2_NB_Q": "Emploi total par profession"}
)

# Liste des codes ISO pour la selection des pays
liste_pays = (
    [p.get("code_iso", p) for p in pays_dispo if isinstance(p, dict)]
    if pays_dispo
    else ["FRA", "DEU", "ESP", "ITA"]
)

# ------------------------------------------------------------------------------
# 2. Formulaire de selection dans la barre laterale
# ------------------------------------------------------------------------------
st.sidebar.header("Configuration du Rapport")

code_indicateur = st.sidebar.selectbox(
    "Indicateur",
    options=list(dict_indicateurs.keys()),
    format_func=lambda x: f"{x} - {dict_indicateurs.get(x, x)}",
)

pays_selectionnes = st.sidebar.multiselect(
    "Pays a comparer",
    options=liste_pays,
    default=["FRA", "DEU"] if len(liste_pays) >= 2 else liste_pays[:1],
)

classif1 = st.sidebar.text_input("Classification (classif1)", value="Total")
sexe = st.sidebar.selectbox("Sexe", options=["Total", "Female", "Male"], index=0)
n_periodes = st.sidebar.slider("Nombre de periodes", min_value=2, max_value=20, value=8)

# ------------------------------------------------------------------------------
# 3. Generation & Telechargement du PDF via l'API Client
# ------------------------------------------------------------------------------
st.subheader("Generation du document")

if st.button("Generer le rapport PDF", type="primary"):
    if not pays_selectionnes:
        st.error("Veuillez selectionner au moins un pays.")
    else:
        with st.spinner("Generation du document PDF par le serveur..."):
            # Appel HTTP vers le backend via l'API Client
            reponse = api_client.telecharger_rapport(
                code_indicateur=code_indicateur,
                pays=pays_selectionnes,
                classif1=classif1,
                sexe=sexe,
                n_periodes=n_periodes,
            )

            if reponse.get("status_code") == 200:
                st.success("Rapport PDF genere avec succes !")
                st.download_button(
                    label="Telecharger le rapport (PDF)",
                    data=reponse["data"],
                    file_name=f"rapport_{code_indicateur}.pdf",
                    mime="application/pdf",
                )
            else:
                st.error(f"Erreur backend ({reponse.get('status_code')}) : {reponse.get('data')}")