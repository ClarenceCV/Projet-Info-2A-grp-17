# Accès à la table observation. Entrée : DataFrame ; sortie : sql (et inversement pour les lectures)

import pandas as pd
from psycopg2.extras import execute_values

from dao.db_connection import DBConnection

# Colonnes du DataFrame propre envoyées dans la table observation (même nom des deux côtés)
COLONNES_OBSERVATION = ["code_iso", "source", "periode", "sexe", "classif1", "valeur", "statut"]

# Colonnes renvoyées par lire() : l'observation + le nom du pays et l'unité de l'indicateur
COLONNES_LECTURE = [
    "indicateur", "code_iso", "nom_pays", "source", "periode",
    "sexe", "classif1", "valeur", "unite", "statut",
]


class ObservationDAO:
    """
    Accès aux observations dans la base de données.
    """

    def enregistrer(self, indicateur_id: int, df: pd.DataFrame) -> int:
        """
        Enregistre les observations d'un indicateur en une seule transaction.
        Si une observation existe déjà (même clé primaire), sa valeur et son statut
        sont mis à jour : relancer l'import ne crée pas de doublons.
        Les pays des observations doivent déjà être dans la table pays.

        params:
            indicateur_id: id de l'indicateur dans la base (c.f. IndicateurDAO.enregistrer)
            df: DataFrame propre issu de DataProcessing.parse_data

        Returns:
            int: nombre d'observations insérées ou mises à jour
        """
        if df.empty:
            return 0

        # une ligne du DataFrame -> un tuple (indicateur_id, code_iso, source, ..., statut)
        lignes = [(indicateur_id, *ligne) for ligne in df[COLONNES_OBSERVATION].itertuples(index=False)]

        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                execute_values(
                    cursor,
                    "INSERT INTO laborscope.observation "
                    "(indicateur_id, code_iso, source, periode, sexe, classif1, valeur, statut) "
                    "VALUES %s "
                    "ON CONFLICT (indicateur_id, code_iso, source, periode, sexe, classif1) "
                    "DO UPDATE SET valeur = EXCLUDED.valeur, statut = EXCLUDED.statut, "
                    "              date_maj = CURRENT_TIMESTAMP;",
                    lignes,
                    page_size=1000,  # envoi par paquets de 1000 lignes
                )
        return len(lignes)

    def lire(
        self,
        code_indicateur: str,
        pays: list[str] | None = None,
        periode_min: str | None = None,
        periode_max: str | None = None,
        sexe: str | None = None,
        classif1: str | None = None,
        limite: int | None = None,
    ) -> pd.DataFrame:
        """
        Lit les observations d'un indicateur. Chaque filtre laissé à None est ignoré.
        ex : taux d'emploi des femmes de 15-24 ans en France depuis 2024 :
            lire("EMP_5WAP_SEX_AGE_RT_Q", ["FRA"], periode_min="2024Q1",
                 sexe="Female", classif1="15-24")

        params:
            code_indicateur: code de l'indicateur (obligatoire)
            pays: codes ISO, ex : ['FRA', 'DEU']
            periode_min, periode_max: bornes incluses, ex : '2024Q1'
            sexe: 'Total', 'Male' ou 'Female'
            classif1: ex '15-24' ou '22 - Health professionals'
            limite: nombre maximum de lignes renvoyées

        Returns:
            pd.DataFrame: une ligne par observation (colonnes COLONNES_LECTURE),
                          triées par pays, période, sexe et classif1
        """
        # on construit le WHERE à partir des seuls filtres renseignés
        # (les noms de colonnes sont écrits ici en dur : pas de risque d'injection SQL)
        conditions = ["i.code = %(code_indicateur)s"]
        if pays:
            conditions.append("o.code_iso = ANY(%(pays)s)")
        if periode_min is not None:
            conditions.append("o.periode >= %(periode_min)s")
        if periode_max is not None:
            conditions.append("o.periode <= %(periode_max)s")
        if sexe is not None:
            conditions.append("o.sexe = %(sexe)s")
        if classif1 is not None:
            conditions.append("o.classif1 = %(classif1)s")

        requete = (
            "SELECT i.code AS indicateur, o.code_iso, p.nom AS nom_pays, o.source, o.periode, "
            "       o.sexe, o.classif1, o.valeur, i.unite, o.statut "
            "FROM laborscope.observation o "
            "JOIN laborscope.indicateur i ON i.id = o.indicateur_id "
            "JOIN laborscope.pays p ON p.code_iso = o.code_iso "
            "WHERE " + " AND ".join(conditions) + " "
            "ORDER BY o.code_iso, o.periode, o.sexe, o.classif1"
        )
        if limite is not None:
            requete += " LIMIT %(limite)s"

        parametres = {
            "code_indicateur": code_indicateur,
            "pays": pays,
            "periode_min": periode_min,
            "periode_max": periode_max,
            "sexe": sexe,
            "classif1": classif1,
            "limite": limite,
        }

        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(requete + ";", parametres)
                lignes = cursor.fetchall()

        # columns= : garde les bonnes colonnes même si aucune ligne n'est trouvée
        return pd.DataFrame(lignes, columns=COLONNES_LECTURE)
