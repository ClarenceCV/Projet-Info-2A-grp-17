"""Page Streamlit - Rapport PDF (FO3).

Filtres centres, previsualisation integree du PDF et telechargement optionnel.
"""

import base64
import streamlit as st
from utils.api_client import api_client
from utils.auth_guard import exiger_connexion

exiger_connexion()

st.title("Rapport d'Analyse PDF (FO3)")
st.markdown(
    "Configurez vos filtres ci-dessous, previsualisez le rapport genere directement a l'ecran, "
    "puis telechargez-le uniquement s'il vous convient."
)

# ------------------------------------------------------------------------------
# 1. Chargement des metadonnees
# ------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def charger_filtres() -> tuple[dict[str, str], list[str]]:
    res_ind = api_client.get("/indicateurs")
    res_pays = api_client.get("/pays")

    dict_ind = {}
    if res_ind.get("status_code") == 200 and isinstance(res_ind.get("data"), list):
        for ind in res_ind["data"]:
            code = ind.get("code", ind.get("code_indicateur"))
            if code:
                dict_ind[code] = ind.get("libelle", code)

    if not dict_ind:
        dict_ind = {"EMP_5EMP_SEX_OC2_NB_Q": "Emploi total par profession"}

    liste_pays = (
        [p.get("code_iso", p) for p in res_pays["data"] if isinstance(p, dict)]
        if res_pays.get("status_code") == 200 and isinstance(res_pays.get("data"), list)
        else ["FRA", "DEU", "ESP", "ITA"]
    )
    return dict_ind, liste_pays


dict_indicateurs, liste_pays = charger_filtres()

# ------------------------------------------------------------------------------
# 2. Filtres centres dans le corps principal
# ------------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Configuration du Rapport")

    col_top1, col_top2 = st.columns([2, 2])
    with col_top1:
        code_indicateur = st.selectbox(
            "Indicateur principal",
            options=list(dict_indicateurs.keys()),
            format_func=lambda x: f"{x} - {dict_indicateurs.get(x, x)}",
        )
    with col_top2:
        pays_selectionnes = st.multiselect(
            "Pays a comparer",
            options=liste_pays,
            default=["FRA", "DEU"] if len(liste_pays) >= 2 else liste_pays[:1],
        )

    col_bot1, col_bot2, col_bot3 = st.columns(3)
    with col_bot1:
        classif1 = st.text_input("Classification (classif1)", value="15+")
    with col_bot2:
        sexe = st.selectbox("Sexe", options=["Total", "Female", "Male"], index=0)
    with col_bot3:
        n_periodes = st.slider("Nombre de periodes", min_value=2, max_value=20, value=8)

    generer_clic = st.button("Generer l'apercu du rapport", type="primary", width="stretch")

# ------------------------------------------------------------------------------
# 3. Generation, Previsualisation et Telechargement
# ------------------------------------------------------------------------------
if generer_clic:
    if not pays_selectionnes:
        st.error("Veuillez selectionner au moins un pays.")
    else:
        with st.spinner("Generation de l'apercu du rapport PDF..."):
            reponse = api_client.telecharger_rapport(
                code_indicateur=code_indicateur,
                pays=pays_selectionnes,
                classif1=classif1,
                sexe=sexe,
                n_periodes=n_periodes,
            )

            if reponse.get("status_code") == 200:
                st.session_state["fo3_pdf_bytes"] = reponse["data"]
                st.session_state["fo3_pdf_filename"] = f"rapport_{code_indicateur}.pdf"
            else:
                st.error(f"Erreur backend ({reponse.get('status_code')}) : {reponse.get('data')}")

# Affichage persistant de la previsualisation et du bouton de telechargement
if "fo3_pdf_bytes" in st.session_state:
    st.divider()
    col_titre, col_dl = st.columns([3, 1])
    with col_titre:
        st.subheader("Previsualisation du document")
    with col_dl:
        st.download_button(
            label="Telecharger ce PDF",
            data=st.session_state["fo3_pdf_bytes"],
            file_name=st.session_state["fo3_pdf_filename"],
            mime="application/pdf",
            type="primary",
            width="stretch",
        )

    # Encodage Base64 pour l'affichage integre dans le navigateur
    base64_pdf = base64.b64encode(st.session_state["fo3_pdf_bytes"]).decode("utf-8")
    pdf_display = (
        f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
        f'width="100%" height="750" type="application/pdf"></iframe>'
    )
    st.markdown(pdf_display, unsafe_allow_html=True)