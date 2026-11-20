"""
Logique métier de la fonctionnalité F4 : comparaison d'un indicateur entre pays.
Le controller appelle le service, le service appelle le DAO.

Choix pour « la période la plus récente disponible » : option (b)
-> on prend la dernière période DE CHAQUE PAYS (les pays ne sont pas forcément
comparés à la même date : la colonne periode l'indique).
"""

import pandas as pd

from dao.observation_dao import ObservationDAO

# Colonnes renvoyées pour chaque pays du classement
COLONNES_CLASSEMENT = ["rang", "code_iso", "nom_pays", "periode", "valeur", "unite"]


class ComparaisonPaysService:
    """
    Compare un indicateur entre plusieurs pays, à la période la plus récente disponible (F4).
    """

    def comparer_pays(
        self,
        code_indicateur: str,
        classif1: str,
        pays: list[str] | None = None,
        sexe: str = "Total",
        top: int = 3,
        periode: str | None = None,
    ) -> dict:
        """
        Classe les pays selon la valeur de l'indicateur à leur dernière période disponible.
        ex : taux d'emploi total des 15+ en France, Allemagne, Espagne et Italie :
            comparer_pays("EMP_5WAP_SEX_AGE_RT_Q", "15+", ["FRA", "DEU", "ESP", "ITA"])
        Si une période est choisie (ex : '2025Q2'), on prend pour chaque pays sa dernière
        période AVANT ou ÉGALE à celle choisie (jamais une donnée plus récente).

        params:
            code_indicateur: code de l'indicateur, ex : 'EMP_5WAP_SEX_AGE_RT_Q'
            classif1: tranche d'âge ou profession, ex : '15+'
            pays: codes ISO, ex : ['FRA', 'DEU'] (None -> tous les pays de la base)
            sexe: 'Total', 'Male' ou 'Female'
            top: nombre de pays dans plus_hauts et plus_bas
            periode: période choisie, ex : '2025Q2' (None -> dernière période de chaque pays)

        Returns:
            dict: {"periode_reference": str | None (période la plus récente du classement),
                   "periodes_disponibles": list[str] (toutes les périodes, pour le menu de la page),
                   "periode_commune": str | None (dernière période où TOUS les pays ont une donnée),
                   "classement": pd.DataFrame (rang, code_iso, nom_pays, periode, valeur, unite),
                   "plus_hauts": pd.DataFrame (les top premiers),
                   "plus_bas": pd.DataFrame (les top derniers)}
        """
        df = ObservationDAO().lire(code_indicateur, pays, sexe=sexe, classif1=classif1)

        # aucune donnée : on renvoie un résultat vide (pas d'erreur)
        if df.empty:
            vide = pd.DataFrame(columns=COLONNES_CLASSEMENT)
            return {"periode_reference": None,
                    "periodes_disponibles": [],
                    "periode_commune": None,
                    "classement": vide,
                    "plus_hauts": vide,
                    "plus_bas": vide}

        # toutes les périodes présentes (avant le filtre), pour le menu de la page
        periodes_disponibles = sorted(df["periode"].unique())

        # 1. une seule source par pays et par période : on garde la première par ordre alphabétique
        df = df.sort_values(["code_iso", "periode", "source"])
        df = df.drop_duplicates(["code_iso", "periode"], keep="first")

        # dernière période commune : on compte les pays de chaque période,
        # et on garde les périodes où il y a TOUS les pays (None s'il n'y en a aucune)
        nb_pays = df["code_iso"].nunique()
        nb_pays_par_periode = df.groupby("periode")["code_iso"].nunique()
        periodes_communes = nb_pays_par_periode[nb_pays_par_periode == nb_pays].index
        periode_commune = max(periodes_communes) if len(periodes_communes) > 0 else None

        # période choisie : on enlève les périodes plus récentes (ex : '2025Q1' <= '2025Q2')
        if periode is not None:
            df = df[df["periode"] <= periode]

        # 2. dernière période de chaque pays :
        #  tri par période, puis la dernière ligne de chaque pays
        df = df.sort_values("periode")
        df = df.groupby("code_iso").tail(1)

        # 3. tri par valeur décroissante, puis rang 1, 2, 3...
        df = df.sort_values("valeur", ascending=False)
        df["rang"] = range(1, len(df) + 1)
        classement = df[COLONNES_CLASSEMENT].reset_index(drop=True)

        # 4. les top premiers et les top derniers du classement
        plus_hauts = classement.head(top)
        plus_bas = classement.tail(top)

        # 5. période la plus récente parmi celles du classement (None si le classement est vide)
        periode_reference = classement["periode"].max() if not classement.empty else None

        return {
            "periode_reference": periode_reference,
            "periodes_disponibles": periodes_disponibles,
            "periode_commune": periode_commune,
            "classement": classement,
            "plus_hauts": plus_hauts,
            "plus_bas": plus_bas,
        }
