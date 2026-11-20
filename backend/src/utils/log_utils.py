"""Outils de logs techniques : initialisation depuis logging_config.yml et décorateur @log."""

import logging
import logging.config
from functools import wraps
from pathlib import Path

import pandas as pd
import yaml

# Chemin vers le dossier backend
BACKEND_DIR = Path(__file__).resolve().parents[2]

# Dossier des logs
LOG_DIR = BACKEND_DIR / "logs"

# Création automatique du dossier s'il n'existe pas
LOG_DIR.mkdir(parents=True, exist_ok=True)


def initialize_logs(name: str):
    """Initialize logging from a configuration file"""

    # Chemin absolu vers le dossier backend
    backend_dir = Path(__file__).resolve().parents[2]

    # Création du dossier logs
    logs_dir = backend_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Chargement de la configuration YAML
    config_file = backend_dir / "logging_config.yml"

    with open(config_file, encoding="utf-8") as stream:
        config = yaml.safe_load(stream)

    # Remplacement du chemin du fichier de logs
    config["handlers"]["file"]["filename"] = str(
        logs_dir / f"{name}.log"
    )

    logging.config.dictConfig(config)

    logging.info("-" * 50)
    logging.info("Starting %s", name)
    logging.info("-" * 50)


def get_logger(module_name: str, max_size: int = 25):
    """
    Returns a logger with a shortened name based on the module path.
    If the path exceeds max_size, it uses initials for the prefix parts.
    """
    if len(module_name) <= max_size:
        return logging.getLogger(module_name)

    parts = module_name.split(".")
    short_prefix = [p[0] for p in parts[:-1]]
    short_name = ".".join(short_prefix + [parts[-1]])

    return logging.getLogger(short_name)


class LogIndentation:
    """For indenting logs when entering a new method"""

    current_indentation = 0
    indentation_size = 2

    @classmethod
    def increase_indentation(cls):
        """Increase indentation"""
        cls.current_indentation += 1

    @classmethod
    def decrease_indentation(cls):
        """Decrease indentation"""
        cls.current_indentation -= 1

    @classmethod
    def get_indentation(cls):
        """Get the current indentation"""
        return " " * cls.indentation_size * cls.current_indentation


# Paramètres dont la valeur est masquée dans les logs (mots de passe, tokens...)
MOTS_SENSIBLES = {"password", "passwd", "pwd", "pass", "mdp", "token", "secret", "key"}


def _est_sensible(nom_parametre: str) -> bool:
    """True si le nom du paramètre contient un mot sensible (sa valeur ne doit pas être loggée)."""
    return any(mot in nom_parametre.lower() for mot in MOTS_SENSIBLES)


def _parametres_lisibles(func, args: tuple, kwargs: dict) -> tuple:
    """
    Valeurs des paramètres d'un appel de méthode, sensibles remplacées par '*****'.
    args[0] (self) est ignoré.
    """
    noms = func.__code__.co_varnames[1 : func.__code__.co_argcount]
    valeurs = [
        "*****" if _est_sensible(nom) else str(valeur) for nom, valeur in zip(noms, args[1:])
    ]
    valeurs += ["*****" if _est_sensible(nom) else str(v) for nom, v in kwargs.items()]
    return tuple(valeurs)


def _resumer(resultat) -> str:
    """Résumé court d'un résultat pour les logs (taille au lieu du contenu pour les collections)."""
    if isinstance(resultat, pd.DataFrame):
        return f"DataFrame : {len(resultat)} lignes, {len(resultat.columns)} colonnes"
    if isinstance(resultat, list):
        return f"Liste : {len(resultat)} éléments"
    if isinstance(resultat, dict):
        return f"Dictionnaire : {len(resultat)} éléments"
    return str(resultat)


def log(func):
    """Log automatiquement l'entrée, la sortie et les erreurs d'une fonction."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        module = args[0].__class__.__module__ if args else func.__module__
        logger = get_logger(module)

        LogIndentation.increase_indentation()
        indentation = LogIndentation.get_indentation()
        nom = func.__name__

        # %s : le message n'est construit que s'il est vraiment écrit (recommandé par pylint)
        logger.info("%s%s%s - START", indentation, nom, _parametres_lisibles(func, args, kwargs))
        try:
            resultat = func(*args, **kwargs)
            logger.info("%s%s - END", indentation, nom)
            logger.info("%s  └─> Output: %s", indentation, _resumer(resultat))
            return resultat
        except Exception:
            logger.exception("%s%s - ERROR", indentation, nom)
            raise
        finally:
            LogIndentation.decrease_indentation()

    return wrapper
