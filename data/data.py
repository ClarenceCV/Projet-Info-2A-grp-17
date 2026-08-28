import requests
import pandas as pd
from io import StringIO

# lien pour le code : https://rtavenar.github.io/poly_python/content/api.html

url = "https://rplumber.ilo.org/data/indicator?id=EMP_5EMP_SEX_OC2_NB_Q&timefrom=2020&timeto=2026&type=label&format=.csv"

reponse = requests.get(url)
print(reponse) # si renvoie 200 Ok

# Transformer la réponse CSV en DataFrame
df_EMP_5EMP_SEX_OC2_NB_Q = pd.read_csv(StringIO(reponse.text))

print(df_EMP_5EMP_SEX_OC2_NB_Q)
