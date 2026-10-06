# Configuration de l'import ILOSTAT : le seul endroit à modifier pour suivre
# un nouvel indicateur ou un nouveau pays.

from business_object.indicateur import Indicateur

INDICATEURS = [
    Indicateur(
        code="EMP_5EMP_SEX_OC2_NB_Q",
        libelle="Emploi par sexe et profession",
        unite="milliers",
        frequence="Q",
        nom_classif1="profession",
    ),
    Indicateur(
        code="EMP_5WAP_SEX_AGE_RT_Q",
        libelle="Taux d'emploi par sexe et âge",
        unite="%",
        frequence="Q",
        nom_classif1="tranche_age",
    ),
]

# Pour tester, ensuite on importe tout
# Codes ISO des pays importés (les noms des pays arrivent avec les données de l'API)
PAYS_SUIVIS = ["FRA", "DEU", "ESP", "ITA"]

# Première année importée
ANNEE_DEBUT = 2020
