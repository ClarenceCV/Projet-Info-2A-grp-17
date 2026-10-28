# Menus déroulants communs à toutes les pages d'analyse (évolution, comparaison, carte, multi-indicateurs...).
# Chaque fonction affiche un menu et renvoie le choix de l'utilisateur.
#
# Utilisation dans une page :
#     from utils.selecteurs import choisir_indicateur, choisir_pays, choisir_sexe, choisir_classif1
#
#     indicateur = choisir_indicateur()               # ex : 'EMP_5WAP_SEX_AGE_RT_Q'
#     pays = choisir_pays()                           # ex : ['FRA', 'ESP']
#     classif1 = choisir_classif1(indicateur)         # ex : '15+'
#     sexe = choisir_sexe()                           # ex : 'Total'
#
# Si une page affiche deux fois le même menu (ex : multi-indicateurs), donner un paramètre `cle`
# différent à chaque fois (ex : cle="serie1", cle="serie2").

import streamlit as st

from utils.api_client import api_client

# Libellés français des valeurs de la colonne sexe (les valeurs envoyées à l'API restent en anglais)
LIBELLES_SEXE = {"Total": "Total", "Male": "Hommes", "Female": "Femmes"}

# Valeurs de classif1 proposées par défaut si elles existent (le « total » de chaque indicateur)
CLASSIF1_PAR_DEFAUT = ["Total", "15+"]


# --- Lecture des listes depuis l'API (mises en cache) -------------------------------------


@st.cache_data(ttl=600, show_spinner=False)
def _lire(chemin: str):
    """
    Appelle l'API et renvoie les données. Le résultat est gardé en mémoire 10 minutes (ttl=600) :
    Streamlit réexécutant toute la page à chaque clic, l'API n'est pas rappelée à chaque fois.

    Raises:
        RuntimeError: si l'API ne répond pas correctement (une erreur n'est jamais mise en cache)
    """
    reponse = api_client.get(chemin)
    if reponse["status_code"] != 200:
        raise RuntimeError(f"{chemin} : {reponse['data']}")
    return reponse["data"]


def _lire_ou_afficher_erreur(chemin: str):
    """Comme _lire, mais affiche l'erreur dans la page et renvoie None au lieu de planter."""
    try:
        return _lire(chemin)
    except RuntimeError as e:
        st.error(f"Impossible de charger la liste : {e}")
        return None


# --- Les menus ---------------------------------------------------------------------------


def choisir_indicateur(cle: str = "") -> str | None:
    """
    Menu de choix d'un indicateur (affiche le libellé, renvoie le code).

    Returns:
        str | None: code de l'indicateur, ex 'EMP_5WAP_SEX_AGE_RT_Q' (None si la liste est vide)
    """
    indicateurs = _lire_ou_afficher_erreur("/indicateurs")
    if not indicateurs:
        return None

    libelles = {i["code"]: f"{i['libelle']} ({i['unite']})" for i in indicateurs}
    return st.selectbox(
        "Indicateur",
        options=list(libelles),               # les valeurs renvoyées : les codes
        format_func=lambda code: libelles[code],  # ce qui est affiché : les libellés
        key=f"indicateur_{cle}",
    )


def choisir_pays(multiple: bool = True, defaut: list[str] | None = None, cle: str = ""):
    """
    Menu de choix d'un ou plusieurs pays (affiche le nom, renvoie le code ISO).

    params:
        multiple: True → plusieurs pays (liste), False → un seul pays
        defaut: codes ISO présélectionnés, ex ['FRA'] (par défaut : la France si elle existe)

    Returns:
        list[str] si multiple (ex ['FRA', 'ESP']), sinon str (ex 'FRA') ; None si la liste est vide
    """
    pays = _lire_ou_afficher_erreur("/pays")
    if not pays:
        return None

    noms = {p["code_iso"]: p["nom_pays"] for p in pays}
    # on ne garde que les valeurs par défaut qui existent vraiment dans la liste
    defaut = [code for code in (defaut or ["FRA"]) if code in noms]

    if multiple:
        return st.multiselect(
            "Pays", options=list(noms), default=defaut,
            format_func=lambda code: noms[code], key=f"pays_{cle}",
        )
    index = list(noms).index(defaut[0]) if defaut else 0
    return st.selectbox(
        "Pays", options=list(noms), index=index,
        format_func=lambda code: noms[code], key=f"pays_{cle}",
    )


def choisir_sexe(cle: str = "") -> str:
    """
    Choix du sexe (affiché en français, renvoie la valeur de la base).

    Returns:
        str: 'Total', 'Male' ou 'Female'
    """
    return st.radio(
        "Sexe", options=list(LIBELLES_SEXE),
        format_func=lambda valeur: LIBELLES_SEXE[valeur],
        horizontal=True, key=f"sexe_{cle}",
    )


def choisir_classif1(code_indicateur: str | None, cle: str = "") -> str | None:
    """
    Choix d'une modalité de classif1 pour un indicateur : une profession ou une tranche d'âge.
    Le « total » de l'indicateur ('Total' ou '15+') est présélectionné.

    Returns:
        str | None: ex '15+' ou '22 - Health professionals' (None si pas d'indicateur choisi)
    """
    if code_indicateur is None:
        return None

    reponse = _lire_ou_afficher_erreur(f"/indicateurs/{code_indicateur}/classif1")
    if not reponse or not reponse["modalites"]:
        return None

    modalites = reponse["modalites"]
    index = next((modalites.index(v) for v in CLASSIF1_PAR_DEFAUT if v in modalites), 0)
    return st.selectbox(
        "Profession / tranche d'âge", options=modalites, index=index,
        key=f"classif1_{cle}_{code_indicateur}",  # nouvel indicateur → nouveau menu (liste différente)
    )
