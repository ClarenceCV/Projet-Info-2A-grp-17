"""Page Streamlit - Fonctionnalité F5 : Comparaison multi-indicateurs en base 100."""

import os
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Configuration de l'URL du backend FastAPI
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")

# Note : Ne pas appeler st.set_page_config() si la page est chargée en sous-page
st.title("F5 — Comparaison Multi-Indicateurs (Base 100)")
st.markdown(
    "Cette page permet de comparer l'évolution temporelle de **2 à 4 indicateurs** "
    "en ramenant leurs valeurs sur une **base 100 commune**."
)


# ------------------------------------------------------------------------------
# 1. Chargement sécurisé des options depuis le backend
# ------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def charger_options() -> tuple[dict[str, str], list[str]]:
    """Récupère la liste des indicateurs et des pays depuis le backend."""
    dict_ind = {
        "EMP_5EMP_SEX_OC2_NB_Q": "Emploi total par profession (Q)",
        "EMP_5WAP_SEX_AGE_RT_Q": "Taux d'emploi par âge (Q)",
    }
    liste_p = ["FRA", "DEU", "ESP", "ITA"]

    try:
        res_ind = requests.get(f"{BACKEND_URL}/indicateurs", timeout=3)
        if res_ind.status_code == 200 and res_ind.json():
            data = res_ind.json()
            dict_ind = {
                item.get("code", item.get("code_indicateur")): item.get(
                    "libelle", item.get("code")
                )
                for item in data
            }

        res_pays = requests.get(f"{BACKEND_URL}/pays", timeout=3)
        if res_pays.status_code == 200 and res_pays.json():
            data_p = res_pays.json()
            liste_p = [p.get("code_iso", p.get("code", p)) for p in data_p]

    except requests.RequestException:
        st.warning(" Impossibilité de joindre les métadonnées. Utilisation des valeurs par défaut.")

    return dict_ind, liste_p


dict_indicateurs, liste_pays = charger_options()

# ------------------------------------------------------------------------------
# 2. Formulaire de configuration des séries (2 à 4)
# ------------------------------------------------------------------------------
st.sidebar.header("⚙️ Configuration des Séries")
nb_series = st.sidebar.number_input(
    "Nombre de séries à comparer",
    min_value=2,
    max_value=4,
    value=2,
    step=1,
    key="nb_series_input",
)

selections = []

for i in range(int(nb_series)):
    with st.sidebar.expander(f" Série {i+1}", expanded=(i < 2)):
        ind_code = st.selectbox(
            "Indicateur",
            options=list(dict_indicateurs.keys()),
            format_func=lambda x, d=dict_indicateurs: f"{x} - {d.get(x, x)}",
            key=f"f5_ind_{i}",
        )
        pays_code = st.selectbox(
            "Pays",
            options=liste_pays,
            index=0,
            key=f"f5_pays_{i}",
        )
        classif1 = st.text_input(
            "Classification (classif1)",
            value="Total" if i == 0 else "15+",
            key=f"f5_classif_{i}",
        )
        sexe = st.selectbox(
            "Sexe",
            options=["Total", "M", "F"],
            index=0,
            key=f"f5_sexe_{i}",
        )

        selections.append(
            {
                "indicateur": str(ind_code),
                "pays": str(pays_code),
                "classif1": str(classif1).strip(),
                "sexe": str(sexe),
            }
        )

# ------------------------------------------------------------------------------
# 3. Exécution de la comparaison
# ------------------------------------------------------------------------------
if st.button(" Lancer la comparaison", type="primary", key="btn_comparer"):
    with st.spinner("Calcul des indices en base 100..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/analyses/multi-indicateurs",
                json=selections,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()

                if not data:
                    st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
                else:
                    df = pd.DataFrame(data)

                    # --- Graphique Plotly ---
                    st.subheader("Évolution comparée (Base 100)")
                    fig = px.line(
                        df,
                        x="periode",
                        y="valeur_base100",
                        color="serie",
                        markers=True,
                        title="Séries ramenées en base 100 (période initiale commune = 100)",
                        labels={
                            "valeur_base100": "Indice (Base 100)",
                            "periode": "Période",
                            "serie": "Série",
                        },
                    )
                    fig.update_layout(
                        hovermode="x unified",
                        legend=dict(orientation="h", y=-0.2),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # --- Tableau récapitulatif ---
                    with st.expander(" Consulter le tableau de données"):
                        st.dataframe(df, use_container_width=True)

            elif response.status_code in (400, 422):
                err_detail = response.json().get("detail", "Erreur de validation.")
                st.error(f" Erreur {response.status_code} : {err_detail}")
            else:
                st.error(f" Erreur serveur ({response.status_code})")

        except requests.RequestException as exc:
            st.error(f"Erreur de connexion au serveur backend : {exc}")