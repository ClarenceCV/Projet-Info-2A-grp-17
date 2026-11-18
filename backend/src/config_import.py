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
    Indicateur(
        code="UNE_5EAP_SEX_AGE_RT_Q",
        libelle="Taux de chômage par sexe et par âge",
        unite="%",
        frequence="Q",
        nom_classif1="tranche_age"
    )
]

# Codes ISO des pays importés (les noms des pays arrivent avec les données de l'API)
PAYS_SUIVIS = [
    "AGO", "ARM", "AUS", "AUT", "BHS", "BGD", "BRB", "BEL", "BLZ", "BIH",
    "BWA", "BRA", "BGR", "CAN", "CHL", "CRI", "HRV", "CYP", "CZE", "DNK",
    "DJI", "ECU", "EGY", "EST", "FIN", "FRA", "GMB", "GEO", "DEU", "GHA",
    "GRC", "GTM", "GUY", "HUN", "ISL", "IDN", "IRL", "ISR", "ITA", "JAM",
    "JPN", "JOR", "KEN", "XKX", "LVA", "LTU", "LUX", "MLT", "MNG", "NLD",
    "NGA", "NOR", "PAK", "POL", "PRT", "KOR", "MDA", "ROU", "RUS", "RWA",
    "SAU", "SRB", "SYC", "SGP", "SVK", "SVN", "ZAF", "ESP", "SWE", "CHE",
    "TZA", "THA", "TTO", "TUN", "GBR", "USA", "URY", "VNM", "ZMB", "ZWE",
]

# Première année importée
ANNEE_DEBUT = 2020
