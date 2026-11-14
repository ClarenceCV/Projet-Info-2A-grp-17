"""Page Streamlit - Comparaison Multi-Indicateurs (F5).

4 series configurables directement au centre de l'ecran, maintien explicite
des selections par l'utilisateur et previsualisation avant telechargement.
"""

import base64
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.api_client import api_client
from utils.auth_guard import exiger_connexion

exiger_connexion()

st.title("Comparaison Multi-Indicateurs (F5)")
st.markdown(
    "Configurez jusqu'a 4 series simultanement. Cochez ou decochez chaque serie "
    "pour l'ajouter ou la retirer du graphique."
)

# ------------------------------------------------------------------------------
# 1. Chargement des metadonnees (Indicateurs et Pays)
# ------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def charger_metadonnees() -> tuple[dict[str, str], list[str]]:
    res_ind = api_client.get("/indicateurs")
    res_pays = api_client.get("/pays")

    dict_ind = {}
    if res_ind.get("status_code") == 200 and isinstance(res_ind.get("data"), list):
        for ind in res_ind["data"]:
            code = ind.get("code", ind.get("code_indicateur"))
            libelle = ind.get("libelle", code)
            if code:
                dict_ind[code] = libelle

    if not dict_ind:
        dict_ind = {
            "EMP_5WAP_SEX_AGE_RT_Q": "Taux d'emploi (15+)",
            "UNE_5UAP_SEX_AGE_RT_Q": "Taux de chomage (15+)",
            "EAP_5EAP_SEX_AGE_RT_Q": "Taux d'activite (15+)",
            "EMP_5EMP_SEX_OC2_NB_Q": "Emploi total par profession",
        }

    liste_pays = (
        [p.get("code_iso", p) for p in res_pays["data"] if isinstance(p, dict)]
        if res_pays.get("status_code") == 200 and isinstance(res_pays.get("data"), list)
        else ["FRA", "DEU", "ESP", "ITA", "USA"]
    )
    return dict_ind, liste_pays


dict_indicateurs, liste_pays = charger_metadonnees()
codes_dispo = list(dict_indicateurs.keys())

# ------------------------------------------------------------------------------
# 2. Panneau central : 4 series visibles et configurables directement
# ------------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Configuration des 4 Series")

    # Option globale en haut du panneau central
    base_100 = st.checkbox(
        "Normaliser les series en Base 100 (recommande pour comparer des unites differentes)",
        value=True,
        key="f5_base_100",
    )

    cols = st.columns(4)
    selections_actives = []

    for i in range(4):
        idx_defaut_ind = i % len(codes_dispo)
        idx_defaut_pays = liste_pays.index("FRA") if "FRA" in liste_pays else 0

        with cols[i]:
            st.markdown(f"**Serie {i + 1}**")
            # L'utilisateur coche ou decoche explicitement la serie
            active = st.checkbox(
                f"Afficher la serie {i + 1}",
                value=True,
                key=f"f5_active_{i}",
            )

            ind_choisi = st.selectbox(
                "Indicateur",
                options=codes_dispo,
                index=idx_defaut_ind,
                key=f"f5_ind_{i}",
                format_func=lambda x: f"{x} - {dict_indicateurs.get(x, x)}",
                disabled=not active,
            )

            pays_choisi = st.selectbox(
                "Pays",
                options=liste_pays,
                index=idx_defaut_pays,
                key=f"f5_pays_{i}",
                disabled=not active,
            )

            classif_choisie = st.text_input(
                "Classification",
                value="15+",
                key=f"f5_classif_{i}",
                disabled=not active,
            )

            sexe_choisi = st.selectbox(
                "Sexe",
                options=["Total", "Female", "Male"],
                index=0,
                key=f"f5_sexe_{i}",
                disabled=not active,
            )

            if active:
                selections_actives.append(
                    {
                        "code_indicateur": ind_choisi,
                        "code_iso": pays_choisi,
                        "classif1": classif_choisie,
                        "sexe": sexe_choisi,
                    }
                )

# ------------------------------------------------------------------------------
# 3. Affichage immediat du graphique comparatif
# ------------------------------------------------------------------------------
if not selections_actives:
    st.info("Cochez au moins une serie ci-dessus pour afficher le graphique.")
else:
    with st.spinner("Actualisation du graphique..."):
        reponse = api_client.post(
            "/analyses/multi-indicateurs",
            json={"selections": selections_actives, "base_100": base_100},
        )

    if reponse.get("status_code") == 200 and reponse.get("data"):
        df = pd.DataFrame(reponse["data"])

        if not df.empty:
            df["serie_label"] = df.apply(
                lambda r: f"{r['code_indicateur']} ({r['code_iso']} - {r.get('sexe', '')})",
                axis=1,
            )

            fig = px.line(
                df,
                x="periode",
                y="valeur",
                color="serie_label",
                markers=True,
                title="Evolution Comparative Multi-Indicateurs",
                labels={
                    "periode": "Periode",
                    "valeur": "Indice (Base 100)" if base_100 else "Valeur brute",
                    "serie_label": "Serie",
                },
            )
            fig.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, width="stretch")

            with st.expander("Afficher le tableau des donnees"):
                st.dataframe(df, width="stretch")
        else:
            st.warning("Aucune donnee disponible pour les filtres selectionnes.")
    else:
        st.error(f"Erreur lors de la recuperation des donnees : {reponse.get('data')}")