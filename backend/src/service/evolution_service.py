# Logique métier de la fonctionnalité F3 : évolution d'un indicateur sur les N dernières périodes.
# Le controller appelle le service, le service appelle le DAO (et fait les calculs avec pandas).

import numpy as np
import pandas as pd

from dao.observation_dao import ObservationDAO

# Colonnes renvoyées par le service (une ligne par pays et par période)
COLONNES_EVOLUTION = [
    "code_iso", "nom_pays", "periode", "valeur", "unite", "variation_abs", "variation_pct",
]


class EvolutionService:
    """
    Calcule l'évolution d'un indicateur dans le temps.
    """

    def evolution(
        self,
        code_indicateur: str,
        pays: list[str],              
        classif1: str,
        sexe: str = "Total",
        n_periodes: int = 8
    ) -> pd.DataFrame:
        """
        Évolution d'un indicateur sur les n dernières périodes, pour chaque pays.

        Étapes : une seule source par pays et par période, tri chronologique,
        calcul des variations pays par pays, puis conservation des n dernières périodes.
        Les variations sont calculées AVANT de couper : sinon la première période
        conservée n'aurait pas de variation.

        params:
            code_indicateur: code de l'indicateur, ex : 'EMP_5WAP_SEX_AGE_RT_Q'
            pays: codes ISO, ex : ['FRA', 'ESP']
            classif1: profession ou tranche d'âge, ex : '15+'
            sexe: 'Total', 'Male' ou 'Female'
            n_periodes: nombre de périodes conservées par pays

        Returns:
            pd.DataFrame: colonnes code_iso, nom_pays, periode, valeur, unite,
                          variation_abs, variation_pct (une ligne par pays et période,
                          triées par pays puis période). variation_abs et variation_pct
                          valent NaN pour la première période d'un pays (pas de précédente).
        """
        df = ObservationDAO().lire(code_indicateur, pays, sexe=sexe, classif1=classif1)

        # aucune observation : on renvoie un résultat vide, avec les bonnes colonnes
        if df.empty:
            return pd.DataFrame(columns=COLONNES_EVOLUTION)

        # 1. une seule source par pays et par période : on garde la première par ordre
        #    alphabétique, sinon deux points pour la même date
        df = df.sort_values(["code_iso", "periode", "source"])
        df = df.drop_duplicates(["code_iso", "periode"], keep="first")

        # 2. tri par pays puis période ('2024Q4' : l'ordre alphabétique est chronologique)
        df = df.sort_values(["code_iso", "periode"]).reset_index(drop=True)

        # 3. variations calculées pays par pays (la 1re période de chaque pays vaut NaN)
        precedente = df.groupby("code_iso")["valeur"].shift(1)
        df["variation_abs"] = df["valeur"] - precedente
        # variation en % ; si la valeur précédente vaut 0 le % n'est pas défini -> NaN (pas inf)
        df["variation_pct"] = (df["variation_abs"] / precedente * 100).replace([np.inf, -np.inf], np.nan)

        # 4. on ne garde que les n dernières périodes de chaque pays
        df = df.groupby("code_iso").tail(n_periodes)

        return df[COLONNES_EVOLUTION].reset_index(drop=True)

