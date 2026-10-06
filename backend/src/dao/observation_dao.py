# Accès à la table observation. Entrée : DataFrame ; sortie : sql (et inversement pour les lectures)

import pandas as pd
from psycopg2.extras import execute_values

from dao.db_connection import DBConnection

# Colonnes du DataFrame propre envoyées dans la table observation (même nom des deux côtés)
COLONNES_OBSERVATION = ["code_iso", "source", "periode", "sexe", "classif1", "valeur", "statut"]


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
