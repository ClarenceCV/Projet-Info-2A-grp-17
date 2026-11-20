"""Préparation commune des tests DAO : ces tests utilisent une VRAIE base de données PostgreSQL
(celle d'Onyxia, ou une base de test).

Pour ne pas abîmer les vraies données, les tests n'utilisent que des données de test reconnaissables
:
    pays 'ZZZ', indicateur 'TEST_DAO', pseudos commençant par 'test_dao'
et elles sont supprimées avant ET après chaque test (fixture nettoyer_base ci-dessous).

Si la base est injoignable (ex : sur un PC personnel ou sur GitHub), les tests DAO sont
ignorés (SKIPPED) avec la raison affichée, au lieu d'échouer : les autres tests restent utilisables.

Lancement (depuis le dossier backend) :
    uv run pytest src/tests/test_dao -rs        (-rs : affiche la raison des tests ignorés)
"""

import os

import dotenv
import psycopg2
import pytest

from dao.db_connection import DBConnection, parametres_connexion

# Charge le .env SANS écraser les variables déjà définies : on peut ainsi viser une base de test
# en définissant les POSTGRES_* avant de lancer pytest (c'est ce que fait la CI).
dotenv.load_dotenv()

# Données de test (jamais des vraies données)
PAYS_TEST = "ZZZ"
INDICATEUR_TEST = "TEST_DAO"
PSEUDO_TEST = "test_dao"


def raison_base_injoignable() -> str | None:
    """
    Essaie de se connecter à la base (3 secondes maximum).

    Returns:
        str | None: None si la base répond, sinon la raison pour laquelle les tests sont ignorés
    """
    if not os.getenv("POSTGRES_HOST"):
        return "POSTGRES_HOST non défini (pas de base de données configurée)"
    try:
        psycopg2.connect(**parametres_connexion(), connect_timeout=3).close()
    except (psycopg2.OperationalError, KeyError) as e:
        return f"base de données injoignable ({str(e).strip().splitlines()[0]})"
    return None


RAISON_SKIP = raison_base_injoignable()  # calculée une seule fois, au chargement du fichier


def pytest_collection_modifyitems(items):
    """Hook pytest : si la base est injoignable, marque tous les tests DAO comme ignorés."""
    if RAISON_SKIP is None:
        return
    for item in items:
        if "test_dao" in item.path.parts:
            item.add_marker(pytest.mark.skip(reason=RAISON_SKIP))


def supprimer_donnees_de_test():
    """Supprime toutes les données de test de la base."""
    with DBConnection().connection as connection:  # noqa: SIM117
        with connection.cursor() as cursor:
            # les observations de l'indicateur de test sont supprimées avec lui (ON DELETE CASCADE)
            cursor.execute(
                "DELETE FROM laborscope.indicateur WHERE code = %(code)s;",
                {"code": INDICATEUR_TEST},
            )
            cursor.execute(
                "DELETE FROM laborscope.pays WHERE code_iso = %(code)s;", {"code": PAYS_TEST}
            )
            cursor.execute("DELETE FROM laborscope.journal WHERE pseudo LIKE 'test_dao%';")
            cursor.execute("DELETE FROM laborscope.utilisateur WHERE pseudo LIKE 'test_dao%';")


@pytest.fixture(autouse=True)
def nettoyer_base():
    """Avant et après chaque test : supprime les données de test."""
    supprimer_donnees_de_test()
    yield  # le test s'exécute ici
    supprimer_donnees_de_test()
