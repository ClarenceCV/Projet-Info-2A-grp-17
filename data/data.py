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
    if print(reponse) != 200:
        raise ValueError("Il y a une erreur de connection avec le serveur")
    data = pd.read_csv(StringIO(reponse.text))
    return data

# Exemple d'utilisation:
# data_01 = load_data(url = "https://rplumber.ilo.org/data/indicator?id=EMP_5EMP_SEX_OC2_NB_Q&timefrom=2020&timeto=2026&type=label&format=.csv")
# print(data_01)
# ref_area.label               source.label  ...  note_indicator.label                                  note_source.label
# 0              Angola    LFS - Employment Survey  ...  Frequency: Quarterly  Repository: ILO-STATISTICS - Micro data proces...
# 1              Angola    LFS - Employment Survey  ...  Frequency: Quarterly  Repository: ILO-STATISTICS - Micro data proces...
# ...
