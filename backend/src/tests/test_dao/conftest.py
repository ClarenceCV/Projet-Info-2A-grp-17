# Préparation commune des tests DAO : ces tests utilisent la VRAIE base de données (à lancer sur Onyxia).
#
# Pour ne pas abîmer les vraies données, les tests n'utilisent que des données de test reconnaissables :
#     pays 'ZZZ', indicateur 'TEST_DAO', pseudos commençant par 'test_dao'
# et elles sont supprimées avant ET après chaque test (fixture nettoyer_base ci-dessous).
#
# Lancement (depuis la racine du projet) :
#     uv run pytest backend/src/tests/test_dao

import os

import dotenv
import pytest

from dao.db_connection import DBConnection

dotenv.load_dotenv(override=True)  # charge le .env avant la connexion à la base

# Sans base de données (ex : sur GitHub), les tests DAO sont ignorés
if not os.getenv("POSTGRES_HOST"):
    collect_ignore_glob = ["test_*.py"]

# Données de test (jamais des vraies données)
PAYS_TEST = "ZZZ"
INDICATEUR_TEST = "TEST_DAO"
PSEUDO_TEST = "test_dao"


def supprimer_donnees_de_test():
    """Supprime toutes les données de test de la base."""
    with DBConnection().connection as connection:  # noqa: SIM117
        with connection.cursor() as cursor:
            # les observations de l'indicateur de test sont supprimées avec lui (ON DELETE CASCADE)
            cursor.execute("DELETE FROM laborscope.indicateur WHERE code = %(code)s;", {"code": INDICATEUR_TEST})
            cursor.execute("DELETE FROM laborscope.pays WHERE code_iso = %(code)s;", {"code": PAYS_TEST})
            cursor.execute("DELETE FROM laborscope.journal WHERE pseudo LIKE 'test_dao%';")
            cursor.execute("DELETE FROM laborscope.utilisateur WHERE pseudo LIKE 'test_dao%';")


@pytest.fixture(autouse=True)
def nettoyer_base():
    """Avant et après chaque test : supprime les données de test."""
    supprimer_donnees_de_test()
    yield  # le test s'exécute ici
    supprimer_donnees_de_test()
