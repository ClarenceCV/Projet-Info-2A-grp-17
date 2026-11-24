"""
Construit l'URL ILOSTAT d'un indicateur et récupère les données de cette API
sous forme de DataFrame.
"""


from io import StringIO

import pandas as pd
import requests

from utils.log_utils import log

# lien pour le code : https://rtavenar.github.io/poly_python/content/api.html

URL_ILOSTAT = "https://rplumber.ilo.org/data/indicator"


@log
def construire_url(code_indicateur: str, annee_debut: int = 2020) -> str:
    """
    Construit l'url de l'API ILOSTAT pour un indicateur.
    type=both : on récupère à la fois les codes (ex : 'FRA') et les libellés (ex : 'France')

    Args:
        code_indicateur (str): code ILOSTAT de l'indicateur, ex : 'EMP_5EMP_SEX_OC2_NB_Q'
        annee_debut (int): première année récupérée

    Returns:
        str: l'url du fichier CSV de l'indicateur
    """
    return f"{URL_ILOSTAT}?id={code_indicateur}&timefrom={annee_debut}&type=both&format=.csv"


@log
def load_data(url: str) -> pd.DataFrame:
    """
    Télécharge un fichier de données ILOSTAT et le met sous forme de DataFrame.

    Args:
        url (str): url de l'API ILOSTAT (c.f. construire_url)

    Returns:
        pd.DataFrame: les données brutes, avec les colonnes de l'API ILOSTAT

    Raises:
        requests.HTTPError: l'API a répondu par une erreur (code HTTP différent de 200)
        ValueError: l'API a renvoyé une réponse vide
    """
    reponse = requests.get(url, timeout=300)
    reponse.raise_for_status()  # erreur si le code HTTP n'est pas 200
    if not reponse.text.strip():
        raise ValueError(f"L'API ILOSTAT a renvoyé une réponse vide : {url}")

    data = pd.read_csv(StringIO(reponse.text), low_memory=False)
    return data


def get_columns_info(data: pd.DataFrame) -> list[str]:
    """
    Affiche les colonnes disponibles dans le DataFrame ainsi que
    quelques infos utiles pour décider lesquelles garder.

    Args:
        data (pd.DataFrame): DataFrame issu de load_data()

    Returns:
        list[str]: les noms des colonnes
    """
    print(f"Nombre de colonnes : {len(data.columns)}")
    print(f"Nombre de lignes : {len(data)}\n")

    for col in data.columns:
        n_unique = data[col].nunique()
        exemple = data[col].dropna().iloc[0] if data[col].notna().any() else None
        print(f"- {col:<25} | valeurs uniques: {n_unique:<6} | exemple: {exemple}")

    return list(data.columns)


def filter_columns(
    data: pd.DataFrame, colonnes_a_garder: list[str], renommage: list[str] | None = None
) -> pd.DataFrame:
    """
    Filtre les colonnes d'un DataFrame pour ne garder que celles spécifiées,
    avec possibilité de les renommer.

    Args:
        data (pd.DataFrame): DataFrame issu de load_data()
        colonnes_a_garder (list[str]): colonnes à conserver
        renommage (list[str] | None): nouveaux noms, dans le même ordre que colonnes_a_garder
            (même longueur obligatoire)

    Returns:
        pd.DataFrame: copie de data avec les seules colonnes présentes, éventuellement renommées

    Raises:
        ValueError: renommage n'a pas la même longueur que colonnes_a_garder
    """
    manquantes = [c for c in colonnes_a_garder if c not in data.columns]
    if manquantes:
        print(f"Attention, colonnes absentes du dataframe : {manquantes}")

    colonnes_presentes = [c for c in colonnes_a_garder if c in data.columns]
    data_filtree = data[colonnes_presentes].copy()

    if renommage is not None:
        if len(renommage) != len(colonnes_a_garder):
            raise ValueError(
                f"renommage ({len(renommage)} éléments) doit avoir la même "
                f"longueur que colonnes_a_garder ({len(colonnes_a_garder)} éléments)"
            )
        # on garde uniquement les nouveaux noms correspondant aux colonnes présentes
        mapping = dict(zip(colonnes_a_garder, renommage))
        nouveaux_noms = [mapping[c] for c in colonnes_presentes]
        data_filtree.columns = nouveaux_noms

    return data_filtree


# Exemple d'utilisation (seulement si on lance ce fichier directement, pas lors d'un import) :


if __name__ == "__main__":
    data_df = load_data(url=construire_url("EMP_5EMP_SEX_OC2_NB_Q"))
    get_columns_info(data_df)
    # On choisit les colonnes que l'on veut et leurs noms
    colonnes_keep = [
        "ref_area.label",
        "source.label",
        "sex.label",
        "classif1.label",
        "time",
        "obs_value",
    ]
    rename = ["area", "source", "sex", "profession", "date", "value"]
    # On filtre
    data_df = filter_columns(data=data_df, colonnes_a_garder=colonnes_keep, renommage=rename)
    print(data_df)
