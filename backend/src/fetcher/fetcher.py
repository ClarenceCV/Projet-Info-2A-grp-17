import requests
import pandas as pd
from io import StringIO

# lien pour le code : https://rtavenar.github.io/poly_python/content/api.html

url = "https://rplumber.ilo.org/data/indicator?id=EMP_5EMP_SEX_OC2_NB_Q&timefrom=2020&timeto=2026&type=label&format=.csv"

def load_data(url):
    '''
    permet de récupérer des fichiers de données venant de ILOSTAT pour les mettre sous forme de dataframe

    params:
        url: chr
            API venant de ILOSTAT
    '''
    reponse = requests.get(url)
    print(type(print(reponse))) # Attention erreur si != 200

    data = pd.read_csv(StringIO(reponse.text))
    return data


def get_columns_info(data):
    '''
    Affiche les colonnes disponibles dans le dataframe ainsi que
    quelques infos utiles pour décider lesquelles garder.

    params:
        data: pd.DataFrame
            dataframe issu de load_data()
    '''
    print(f"Nombre de colonnes : {len(data.columns)}")
    print(f"Nombre de lignes : {len(data)}\n")

    for col in data.columns:
        n_unique = data[col].nunique()
        exemple = data[col].dropna().iloc[0] if data[col].notna().any() else None
        print(f"- {col:<25} | valeurs uniques: {n_unique:<6} | exemple: {exemple}")

    return list(data.columns)


def filter_columns(data, colonnes_a_garder, renommage=None):
    '''
    Filtre les colonnes d'un dataframe pour ne garder que celles spécifiées,
    avec possibilité de les renommer.

    params:
        data: pd.DataFrame
            dataframe issu de load_data()
        colonnes_a_garder: list[str]
            liste des colonnes à conserver
        renommage: list[str], optionnel
            liste des nouveaux noms, dans le même ordre que colonnes_a_garder
            (doit avoir la même longueur)
    '''
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

# Exemple d'utilisation:

data = load_data(url="https://rplumber.ilo.org/data/indicator?id=EMP_5EMP_SEX_OC2_NB_Q&timefrom=2020&timeto=2026&type=label&format=.csv")
get_columns_info(data)
# On choisit les colonnes que l'on veut et leurs noms
colonnes_keep = ["ref_area.label", "source.label", "sex.label", "classif1.label", "time", "obs_value"]
rename = ["area", "source", "sex", "profession", "date", "value"]
# On filtre
data = filter_columns(data=data, colonnes_a_garder=colonnes_keep, renommage=rename) 
print(data)
