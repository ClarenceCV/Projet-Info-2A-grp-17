# Logique métier de F5 : comparaison de plusieurs indicateurs sur un même même graphique

import pandas as pd
from business_object.selection import Selection
from dao.indicateur_dao import IndicateurDAO
from dao.observation_dao import ObservationDAO


class MultiIndicateursService:
    """Compare l'évolution de plusieurs indicateurs, ramenés en base 100 (F5)."""

    def __init__(self):
        self.indicateur_dao = IndicateurDAO()
        self.observation_dao = ObservationDAO()

    def comparer(self, selections: list[Selection]) -> pd.DataFrame:
        # 1. Vérification préalable des indicateurs et de leurs fréquences
        frequences = set()
        indicateurs_valides = []

        for sel in selections:
            ind = self.indicateur_dao.trouver_par_code(sel.indicateur)
            if not ind:
                raise ValueError(f"Indicateur inconnu : {sel.indicateur}")
            frequences.add(ind.frequence)
            indicateurs_valides.append((sel, ind))

        # Vérification immédiate de la cohérence des fréquences
        if len(frequences) > 1:
            raise ValueError("Les indicateurs ont des fréquences différentes.")

        # 2. Lecture des observations en BDD
        dfs = []
        for sel, ind in indicateurs_valides:
            df = self.observation_dao.lire(
                sel.indicateur, [sel.pays], sexe=sel.sexe, classif1=sel.classif1
            )
            if df.empty:
                continue

            df = df.drop_duplicates(subset=["periode"]).copy()
            libelle = ind.libelle or sel.indicateur
            df["serie"] = f"{libelle} — {sel.pays} — {sel.sexe} — {sel.classif1}"
            df["indicateur"] = sel.indicateur
            dfs.append(df)

        if not dfs:
            return pd.DataFrame(
                columns=[
                    "serie",
                    "indicateur",
                    "periode",
                    "valeur",
                    "unite",
                    "valeur_base100",
                ]
            )

        # 3. Concaténation et traitement de la base 100
        df_concat = pd.concat(dfs, ignore_index=True)
        debut = df_concat.groupby("serie")["periode"].min().max()
        df_filtered = df_concat[df_concat["periode"] >= debut].copy()

        df_filtered = df_filtered.sort_values(by=["serie", "periode"])
        premiere_valeur = df_filtered.groupby("serie")["valeur"].transform("first")
        df_filtered["valeur_base100"] = (df_filtered["valeur"] / premiere_valeur) * 100

        cols = ["serie", "indicateur", "periode", "valeur", "unite", "valeur_base100"]
        return df_filtered[cols]