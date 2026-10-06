# Accès à la table pays. Entrée : DataFrame ; sortie : sql

import pandas as pd
from psycopg2.extras import execute_values

from dao.db_connection import DBConnection


class PaysDAO:
    """
    Accès aux pays dans la base de données.
    """

    def enregistrer(self, df_pays: pd.DataFrame) -> int:
        """
        Enregistre des pays. Ceux qui existent déjà (même code ISO) sont ignorés.

        params:
            df_pays: DataFrame avec les colonnes code_iso et nom_pays
                     ex : FRA | France

        Returns:
            int: nombre de pays envoyés à la base
        """
        if df_pays.empty:
            return 0

        lignes = list(df_pays[["code_iso", "nom_pays"]].drop_duplicates().itertuples(index=False))

        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                execute_values(
                    cursor,
                    "INSERT INTO laborscope.pays (code_iso, nom) VALUES %s "
                    "ON CONFLICT (code_iso) DO NOTHING;",
                    lignes,
                )
        return len(lignes)
