""" Ce fichier sert à se connecter proprement à la base de donnée sql """

import os  # pour accéder aux variables d'environnement

import psycopg2  # librairie essentielle pour faire le lien entre SQL et notre backend
from psycopg2.extras import (
    RealDictCursor,  # pour que le cursor puisse renvoyer un format dictionnaire propre
)

from utils.log_utils import log
from utils.singleton import (
    Singleton,  # empêche de créer plus d'une instance de DBConnection (on n'en veut qu'une)
)


def parametres_connexion() -> dict[str, str]:
    """
    Paramètres de connexion à PostgreSQL, lus dans les variables d'environnement (fichier .env).
    Utilisée aussi par les tests DAO pour vérifier que la base répond.

    Returns:
        dict[str, str]: host, port, database, user et password (pour psycopg2.connect)

    Raises:
        KeyError: si une variable POSTGRES_* est absente
    """
    return {
        "host": os.environ["POSTGRES_HOST"],
        "port": os.environ["POSTGRES_PORT"],
        "database": os.environ["POSTGRES_DATABASE"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
    }


class DBConnection(metaclass=Singleton):
    """Database connection manager implementing the Singleton pattern.

    This class ensures that only a single connection to the PostgreSQL
    database is opened and shared throughout the application lifecycle.

    Attributes:
        connection (psycopg2.extensions.connection): The active database
            connection instance.
    """

    def __init__(self):
        """Initializes the database connection using environment variables.
        Raises:
            KeyError: If any of the required POSTGRES_* environment variables are missing.
            psycopg2.Error: If the connection to the database fails.
        """

        self.__connection = psycopg2.connect(
            **parametres_connexion(),
            options=f"-c search_path={os.environ['POSTGRES_SCHEMA']}",
            cursor_factory=RealDictCursor,
        )

    @property
    @log
    def connection(self):
        """Provides access to the underlying database connection.
        Returns:
            The established database connection.
        """
        return self.__connection
