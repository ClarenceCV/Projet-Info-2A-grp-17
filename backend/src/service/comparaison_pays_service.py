# Logique métier de la fonctionnalité F4 : comparaison d'un indicateur entre pays.
# Le controller appelle le service, le service appelle le DAO.
#
# Choix pour « la période la plus récente disponible » : option (b)
# -> on prend la dernière période DE CHAQUE PAYS (les pays ne sont pas forcément
#    comparés à la même date : la colonne periode l'indique).

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
    ) -> dict:
        """
        Classe les pays selon la valeur de l'indicateur à leur dernière période disponible.
        ex : taux d'emploi total des 15+ en France, Allemagne, Espagne et Italie :
            comparer_pays("EMP_5WAP_SEX_AGE_RT_Q", "15+", ["FRA", "DEU", "ESP", "ITA"])

        params:
            code_indicateur: code de l'indicateur, ex : 'EMP_5WAP_SEX_AGE_RT_Q'
            classif1: tranche d'âge ou profession, ex : '15+'
            pays: codes ISO, ex : ['FRA', 'DEU'] (None -> tous les pays de la base)
            sexe: 'Total', 'Male' ou 'Female'
            top: nombre de pays dans plus_hauts et plus_bas

        Returns:
            dict: {"periode_reference": str | None (période la plus récente du classement),
                   "classement": pd.DataFrame (rang, code_iso, nom_pays, periode, valeur, unite),
                   "plus_hauts": pd.DataFrame (les top premiers),
                   "plus_bas": pd.DataFrame (les top derniers)}
        """
        df = ObservationDAO().lire(code_indicateur, pays, sexe=sexe, classif1=classif1)

        # aucune donnée : on renvoie un résultat vide (pas d'erreur)
        if df.empty:
            vide = pd.DataFrame(columns=COLONNES_CLASSEMENT)
            return {"periode_reference": None, "classement": vide, "plus_hauts": vide, "plus_bas": vide}

        # 1. une seule source par pays et par période : on garde la première par ordre alphabétique
        df = df.sort_values(["code_iso", "periode", "source"])
        df = df.drop_duplicates(["code_iso", "periode"], keep="first")

        # 2. dernière période de chaque pays : tri par période, puis la dernière ligne de chaque pays
        df = df.sort_values("periode")
        df = df.groupby("code_iso").tail(1)

        # 3. tri par valeur décroissante, puis rang 1, 2, 3...
        df = df.sort_values("valeur", ascending=False)
        df["rang"] = range(1, len(df) + 1)
        classement = df[COLONNES_CLASSEMENT].reset_index(drop=True)

        # 4. les top premiers et les top derniers du classement
        plus_hauts = classement.head(top)
        plus_bas = classement.tail(top)

        # 5. période la plus récente parmi celles du classement
        periode_reference = classement["periode"].max()

        return {
            "periode_reference": periode_reference,
            "classement": classement,
            "plus_hauts": plus_hauts,
            "plus_bas": plus_bas,
        }
