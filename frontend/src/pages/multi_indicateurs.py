"""Page Streamlit - Comparaison Multi-Indicateurs (F5).

4 series configurables directement au centre de l'ecran, maintien explicite
des selections par l'utilisateur et previsualisation avant telechargement.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import exiger_connexion

exiger_connexion()

st.title("Comparaison Multi-Indicateurs (F5)")
st.markdown(
    "Configurez jusqu'à 4 séries simultanément. Cochez ou décochez chaque série "
    "pour l'ajouter ou la retirer du graphique."
)

# ------------------------------------------------------------------------------
# 1. Chargement des metadonnees (Indicateurs et Pays)
# ------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def charger_metadonnees() -> tuple[dict[str, str], list[str]]:
    """
    Indicateurs et pays disponibles, lus dans l'API (mis en cache une heure).

    Returns:
        tuple[dict[str, str], list[str]]: {code: libellé} des indicateurs, et codes ISO des pays
    """
    res_ind = api_client.get("/indicateurs")
    res_pays = api_client.get("/pays")

    dict_ind = {}
    if res_ind.get("status_code") == 200 and isinstance(res_ind.get("data"), list):
        for ind in res_ind["data"]:
            code = ind.get("code", ind.get("code_indicateur"))
            libelle = ind.get("libelle") or ind.get("nom") or code
            unite = ind.get("unite")
            if code:
                dict_ind[code] = f"{libelle} ({unite})" if unite else libelle

    if not dict_ind:
        dict_ind = {
            "EMP_5WAP_SEX_AGE_RT_Q": "Taux d'emploi (15+)",
            "UNE_5UAP_SEX_AGE_RT_Q": "Taux de chômage (15+)",
            "EAP_5EAP_SEX_AGE_RT_Q": "Taux d'activité (15+)",
            "EMP_5EMP_SEX_OC2_NB_Q": "Emploi total par profession",
        }

    codes_pays = (
        [p.get("code_iso", p) for p in res_pays["data"] if isinstance(p, dict)]
        if res_pays.get("status_code") == 200 and isinstance(res_pays.get("data"), list)
        else ["FRA", "DEU", "ESP", "ITA", "USA"]
    )
    return dict_ind, codes_pays


@st.cache_data(ttl=3600)
def charger_classif1(code_indicateur: str) -> list[str]:
    """
    Modalités de classif1 disponibles pour un indicateur donné.

    Args:
        code_indicateur (str): code de l'indicateur, ex : 'EMP_5WAP_SEX_AGE_RT_Q'

    Returns:
        list[str]: les modalités (liste vide si l'API est en erreur)
    """
    res = api_client.get(f"/indicateurs/{code_indicateur}/classif1")
    if res.get("status_code") != 200 or not isinstance(res.get("data"), dict):
        return []

    valeurs = []
    for m in res["data"].get("modalites", []):
        # Gère aussi bien une liste de chaînes qu'une liste d'objets
        if isinstance(m, dict):
            m = m.get("classif1", m.get("code", m.get("libelle")))
        if m:
            valeurs.append(m)
    return valeurs

dict_indicateurs, liste_pays = charger_metadonnees()
codes_dispo = list(dict_indicateurs.keys())

# ------------------------------------------------------------------------------
# 2. Panneau central : 4 series visibles et configurables directement
# ------------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Configuration des 4 séries")

    # Option globale en haut du panneau central
    base_100 = st.checkbox(
        "Normaliser les séries en base 100 (recommandé pour comparer des unités différentes)",
        value=True,
        key="f5_base_100",
    )

    cols = st.columns(4)
    selections_actives = []

    for i in range(4):
        idx_defaut_ind = i % len(codes_dispo)
        idx_defaut_pays = liste_pays.index("FRA") if "FRA" in liste_pays else 0

        with cols[i]:
            st.markdown(f"**Série {i + 1}**")
            # L'utilisateur coche ou decoche explicitement la serie
            active = st.checkbox(
                f"Afficher la série {i + 1}",
                value=True,
                key=f"f5_active_{i}",
            )

            ind_choisi = st.selectbox(
                "Indicateur",
                options=codes_dispo,
                index=idx_defaut_ind,
                key=f"f5_ind_{i}",
                format_func=lambda x: f"{dict_indicateurs.get(x, x)} [{x}]",
                disabled=not active,
            )

            pays_choisi = st.selectbox(
                "Pays",
                options=liste_pays,
                index=idx_defaut_pays,
                key=f"f5_pays_{i}",
                disabled=not active,
            )

            classifs_dispo = charger_classif1(ind_choisi)

            if classifs_dispo:
                classif_choisie = st.selectbox(
                    "Classification",
                    options=classifs_dispo,
                    index=0,
                    # La clé inclut l'indicateur : quand il change, le widget est
                    # réinitialisé au lieu de garder une valeur absente des options
                    key=f"f5_classif_{i}_{ind_choisi}",
                    disabled=not active,
                )
            else:
                classif_choisie = None
                st.caption("Aucune classification disponible pour cet indicateur.")

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
    st.info("Cochez au moins une série ci-dessus pour afficher le graphique.")
else:
    with st.spinner("Actualisation du graphique..."):
        reponse = api_client.post(
            "/analyses/multi-indicateurs",
            json={"selections": selections_actives, "base_100": base_100},
        )

    if reponse.get("status_code") == 200 and reponse.get("data"):
        df = pd.DataFrame(reponse["data"])

        if not df.empty:
            if "indicateur" in df.columns:
                df["indicateur"] = df["indicateur"].map(
                    lambda c: f"{dict_indicateurs[c]} [{c}]" if c in dict_indicateurs else c
                )
            if "serie" in df.columns:
                for code_ind, lib_ind in dict_indicateurs.items():
                    df["serie"] = df["serie"].str.replace(code_ind, lib_ind, regex=False)

            colonne_y = "valeur_base100" if base_100 else "valeur"

            fig = px.line(
                df,
                x="periode",
                y=colonne_y,
                color="serie",
                markers=True,
                title="Évolution comparée des indicateurs",
                labels={
                    "periode": "Période",
                    colonne_y: "Indice (base 100)" if base_100 else "Valeur brute",
                    "serie": "Serie",
                },
            )
            fig.update_layout(
                legend={"orientation": "h", "yanchor": "bottom", "y": -0.35,
                        "xanchor": "center", "x": 0.5}
            )
            st.plotly_chart(fig, width="stretch")

            with st.expander("Afficher le tableau des données"):
                st.dataframe(df, width="stretch")
        else:
            st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
    else:
        st.error(f"Erreur lors de la récupération des données : {reponse.get('data')}")
