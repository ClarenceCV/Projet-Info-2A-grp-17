# Réinitialise la base de données : exécute data/init_db.sql (c.f. tp3)
# ATTENTION : supprime et recrée le schéma laborscope, toutes les données sont perdues
#
# Lancement (depuis backend/src) :
#     python -m utils.reset_database

from pathlib import Path

import dotenv

from dao.db_connection import DBConnection

# chemin vers data/init_db.sql, calculé à partir de l'emplacement de ce fichier
CHEMIN_INIT_DB = Path(__file__).resolve().parents[3] / "data" / "init_db.sql"


class ResetDatabase:
    """
    Réinitialisation de la base de données
    """

    def lancer(self):
        """
        Exécute le script init_db.sql : crée le schéma, les tables et les indicateurs.

        Returns:
            bool: True si la réinitialisation a réussi
        """
        script_sql = CHEMIN_INIT_DB.read_text(encoding="utf-8")

        try:
            with DBConnection().connection as connection:  # commit automatique en fin de bloc
                with connection.cursor() as cursor:
                    cursor.execute(script_sql)
        except Exception as e:
            print(f"Erreur lors de la réinitialisation de la base : {e}")
            raise

        return True

    def afficher_tables(self):
        """
        Affiche les tables du schéma laborscope et leur nombre de lignes (pour vérifier la base).
        """
        with DBConnection().connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'laborscope' ORDER BY table_name;"
            )
            tables = [ligne["table_name"] for ligne in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) AS nb FROM laborscope.{table};")
                print(f"  - {table:<12} : {cursor.fetchone()['nb']} ligne(s)")


if __name__ == "__main__":
    dotenv.load_dotenv(override=True)  # charge le .env avant la connexion

    reset = ResetDatabase()
    reset.lancer()
    print("Base de données réinitialisée. Tables du schéma laborscope :")
    reset.afficher_tables()
