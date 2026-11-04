import logging
import logging.config
import pandas as pd
from functools import wraps
from pathlib import Path

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
    logging.info(f"Starting {name}")
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


def log(func):
    """Log automatiquement l'entrée, la sortie et les erreurs d'une fonction."""

    SENSITIVE_KEYWORDS = {
        "password", "passwd", "pwd", "pass",
        "token", "secret", "key",
    }

    @wraps(func)
    def wrapper(*args, **kwargs):

        if args and hasattr(args[0], "__class__"):
            logger = get_logger(args[0].__class__.__module__)
        else:
            logger = get_logger(func.__module__)

        LogIndentation.increase_indentation()
        indentation = LogIndentation.get_indentation()

        method_name = func.__name__

        # Récupération des paramètres
        param_names = func.__code__.co_varnames[1:func.__code__.co_argcount]
        args_list = []

        for i, arg in enumerate(args[1:]):
            if i >= len(param_names):
                break

            param_name = param_names[i].lower()

            if any(keyword in param_name for keyword in SENSITIVE_KEYWORDS):
                args_list.append("*****")
            else:
                args_list.append(str(arg))

        for k, v in kwargs.items():
            if any(keyword in k.lower() for keyword in SENSITIVE_KEYWORDS):
                args_list.append("*****")
            else:
                args_list.append(str(v))

        args_tuple = tuple(args_list)

        logger.info(f"{indentation}{method_name}{args_tuple} - START")

        try:
            result = func(*args, **kwargs)

            # Résumé du résultat
            if isinstance(result, pd.DataFrame):
                result_str = (
                    f"DataFrame : {len(result)} lignes, "
                    f"{len(result.columns)} colonnes"
                )
            elif isinstance(result, list):
                result_str = f"Liste : {len(result)} éléments"
            elif isinstance(result, dict):
                result_str = f"Dictionnaire : {len(result)} éléments"
            else:
                result_str = str(result)

            logger.info(f"{indentation}{method_name} - END")
            logger.info(f"{indentation}  └─> Output: {result_str}")

            return result

        except Exception:
            logger.exception(f"{indentation}{method_name} - ERROR")
            raise

        finally:
            LogIndentation.decrease_indentation()

    return wrapper
