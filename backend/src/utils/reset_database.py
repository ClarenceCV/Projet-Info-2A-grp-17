# Réinitialise la base de données : exécute data/init_db.sql (les tables, vides, c.f. tp3)
# puis recrée les comptes par défaut (user / user et admin / admin, c.f. utils/comptes_par_defaut.py)
# ATTENTION : supprime et recrée le schéma laborscope, toutes les données sont perdues
#
# Les données s'importent ensuite depuis ILOSTAT (python -m fetcher.charger_donnees).
# En dépannage (API ILOSTAT injoignable, démo hors ligne), l'option --exemple charge aussi
# data/pop_db.sql : un petit extrait de vraies données ILOSTAT.
#
# Lancement (depuis backend/src) :
#     python -m utils.reset_database              # tables vides (cas normal)
#     python -m utils.reset_database --exemple    # tables + jeu de données de dépannage

import sys
from pathlib import Path

import dotenv

from dao.db_connection import DBConnection
from utils.comptes_par_defaut import creer_comptes_par_defaut

# dossier data/ à la racine du projet, calculé à partir de l'emplacement de ce fichier
DOSSIER_DATA = Path(__file__).resolve().parents[3] / "data"
CHEMIN_INIT_DB = DOSSIER_DATA / "init_db.sql"  # crée le schéma et les tables (vides)
CHEMIN_POP_DB = DOSSIER_DATA / "pop_db.sql"    # jeu de données de dépannage (option --exemple)


class ResetDatabase:
    """
    Réinitialisation de la base de données
    """

    def lancer(self, avec_exemple: bool = False):
        """
        Exécute init_db.sql (schéma et tables vides), et pop_db.sql si demandé.

        Args:
            avec_exemple (bool): True pour charger aussi le jeu de données de dépannage (pop_db.sql)

        Returns:
            bool: True si la réinitialisation a réussi
        """
        script_sql = CHEMIN_INIT_DB.read_text(encoding="utf-8")
        if avec_exemple:
            script_sql += "\n" + CHEMIN_POP_DB.read_text(encoding="utf-8")

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

    avec_exemple = "--exemple" in sys.argv
    reset = ResetDatabase()
    reset.lancer(avec_exemple=avec_exemple)
    if avec_exemple:
        print("Jeu de données de dépannage chargé (data/pop_db.sql).")
    print("Comptes par défaut :")
    creer_comptes_par_defaut()
    print("Base de données réinitialisée. Tables du schéma laborscope :")
    reset.afficher_tables()
