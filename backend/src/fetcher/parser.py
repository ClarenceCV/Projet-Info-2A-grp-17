# Le fetcher a récupéré les données au format df
# Le parser sert à transformer ces df pour gérer les valeurs manquantes, reformater.. En sortie on doit avoir un df propre
# dont les colonnes sont parfaitement alignées avec nos business_object
# La fonction "mapper" transforme ensuite le df propre en objets python (Observation)

import pandas as pd

from business_object.indicateur import Indicateur
from business_object.observation import Observation
from business_object.pays import Pays
from business_object.profession import Profession

# Colonnes du CSV ILOSTAT à garder -> nom dans notre df propre
# (le fetcher doit utiliser type=both pour avoir à la fois ref_area (code) et ref_area.label (nom))
COLONNES_ILOSTAT = {
    "ref_area": "code_iso",
    "ref_area.label": "nom_pays",
    "source.label": "source",
    "sex.label": "sexe",
    "classif1.label": "classif1",
    "time": "periode",
    "obs_value": "valeur",
}

# Colonnes qui identifient une observation (= contrainte UNIQUE de la table observation)
CLE_OBSERVATION = ["code_iso", "sexe", "profession", "tranche_age", "periode"]

FORMAT_PERIODE = r"^\d{4}Q[1-4]$"


def retirer_prefixe(libelle):
    '''
    Retire le préfixe ajouté par ILOSTAT devant les libellés.
    ex : 'Sex: Female' -> 'Female' ; 'Age (Youth, adults): 15-64' -> '15-64'

    params:
        libelle: str | None
    '''
    if pd.isna(libelle):
        return None
    return libelle.split(": ", 1)[-1].strip()


def separer_classif1(classif1):
    '''
    La colonne classif1 contient soit une profession, soit une tranche d'âge selon l'indicateur.
    Renvoie le couple (profession, tranche_age), l'un des deux étant None.
    ex : 'Occupation (ISCO-08): 1. Managers' -> ('1. Managers', None)
         'Age (Youth, adults): 15-64'        -> (None, '15-64')

    params:
        classif1: str | None
    '''
    if pd.isna(classif1):
        return None, None
    valeur = retirer_prefixe(classif1)
    if classif1.startswith("Age"):
        return None, valeur
    return valeur, None


def nettoyer(data):
    '''
    Transforme le df brut d'ILOSTAT en df propre, aligné avec la classe Observation.
    Colonnes en sortie : code_iso, nom_pays, sexe, profession, tranche_age, periode, valeur

    Étapes :
        1. sélection et renommage des colonnes utiles
        2. suppression des lignes sans valeur ou sans pays
        3. conservation des seules périodes trimestrielles ('2024Q1')
        4. retrait des préfixes ILOSTAT ('Sex: Female' -> 'Female')
        5. séparation de classif1 en profession / tranche_age
        6. une seule source par observation (sinon doublons en base)

    params:
        data: pd.DataFrame
            df brut issu de load_data()
    '''
    manquantes = [c for c in COLONNES_ILOSTAT if c not in data.columns]
    if manquantes:
        raise ValueError(
            f"Colonnes absentes du df ILOSTAT : {manquantes} "
            "(le fetcher doit utiliser type=both dans l'url)"
        )

    # 1. sélection et renommage
    df = data[list(COLONNES_ILOSTAT)].rename(columns=COLONNES_ILOSTAT)

    # 2. valeurs manquantes : valeur convertie en nombre, les textes invalides deviennent NaN
    df["valeur"] = pd.to_numeric(df["valeur"], errors="coerce")
    df = df.dropna(subset=["valeur", "code_iso", "nom_pays", "sexe", "periode"])

    # 3. périodes trimestrielles uniquement
    df["periode"] = df["periode"].astype(str).str.strip()
    df = df[df["periode"].str.match(FORMAT_PERIODE)]

    # 4. retrait des préfixes
    df["sexe"] = df["sexe"].map(retirer_prefixe)
    df["source"] = df["source"].fillna("Inconnue")

    # 5. classif1 -> profession / tranche_age
    separation = df["classif1"].map(separer_classif1)
    df["profession"] = separation.map(lambda couple: couple[0])
    df["tranche_age"] = separation.map(lambda couple: couple[1])

    # 6. Parfois on a 2 valeurs provenant de 2 sources différentes donc il faut choisir : on privilégie l'enquête emploi (LFS)
    df["priorite"] = (~df["source"].str.contains("LFS")).astype(int)
    df = df.sort_values(["priorite", "source"]).drop_duplicates(subset=CLE_OBSERVATION, keep="first")

    colonnes_finales = ["code_iso", "nom_pays", "sexe", "profession", "tranche_age", "periode", "valeur"]
    return df[colonnes_finales].sort_values(["code_iso", "periode"]).reset_index(drop=True)


def mapper(data_propre, indicateur):
    '''
    Transforme le df propre en liste d'objets Observation.
    Un même pays / une même profession n'est créé qu'une seule fois (réutilisé entre observations).

    params:
        data_propre: pd.DataFrame
            df issu de nettoyer()
        indicateur: Indicateur
            indicateur auquel appartiennent toutes les lignes du df
    '''
    if not isinstance(indicateur, Indicateur):
        raise TypeError("indicateur should be an Indicateur")

    pays_par_code = {}
    profession_par_libelle = {}
    observations = []

    for ligne in data_propre.itertuples(index=False):
        if ligne.code_iso not in pays_par_code:
            pays_par_code[ligne.code_iso] = Pays(code_iso=ligne.code_iso, nom_pays=ligne.nom_pays)

        profession = None
        if pd.notna(ligne.profession):
            if ligne.profession not in profession_par_libelle:
                profession_par_libelle[ligne.profession] = Profession(libelle_profession=ligne.profession)
            profession = profession_par_libelle[ligne.profession]

        observations.append(
            Observation(
                indicateur=indicateur,
                pays=pays_par_code[ligne.code_iso],
                sexe=ligne.sexe,
                periode=ligne.periode,
                valeur=float(ligne.valeur),
                profession=profession,
                tranche_age=ligne.tranche_age if pd.notna(ligne.tranche_age) else None,
            )
        )

    return observations
