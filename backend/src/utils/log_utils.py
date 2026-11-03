import logging
import logging.config
import numbers
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


def log(func):
    """Decorator to log method calls and their outputs.

    When applied to a method, it logs:
    - the method call with parameter values
    - the return value of the method
    """

    SENSITIVE_KEYWORDS = {
        "password",
        "passwd",
        "pwd",
        "pass",
        "token",
        "secret",
        "key",
    }

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and hasattr(args[0], "__class__"):
            logger = get_logger(f"{args[0].__class__.__module__}")
        else:
            logger = logging.getLogger(__name__)

        LogIndentation.increase_indentation()
        indentation = LogIndentation.get_indentation()

        # Retrieve method parameters
        method_name = func.__name__
        param_names = func.__code__.co_varnames[1 : func.__code__.co_argcount]
        args_list = []

        for i, arg in enumerate(args[1:]):
            if i >= len(param_names):
                break
            param_name = param_names[i].lower()
            if any(keyword in param_name for keyword in SENSITIVE_KEYWORDS):
                args_list.append("*****")
            else:
                args_list.append(str(arg) if not isinstance(arg, numbers.Number) else arg)

        for k, v in kwargs.items():
            if any(keyword in k.lower() for keyword in SENSITIVE_KEYWORDS):
                args_list.append("*****")
            else:
                args_list.append(str(v) if not isinstance(v, numbers.Number) else v)

        args_tuple = tuple(args_list)

        # Log method entry
        logger.info(f"{indentation}{method_name}{args_tuple} - START")
        result = func(*args, **kwargs)
        logger.info(f"{indentation}{method_name}{args_tuple} - END")

        # Shorten long output for readability
        if isinstance(result, list):
            result_str = str([str(item) for item in result[:3]])
            result_str += f" ... ({len(result)} elements)"
        elif isinstance(result, dict):
            result_str = [(str(k), str(v)) for k, v in list(result.items())[:3]]
            result_str += f" ... ({len(result)} elements)"
        elif isinstance(result, str) and len(result) > 50:
            result_str = result[:50] + f" ... ({len(result)} characters)"
        else:
            result_str = str(result)

        logger.info(f"{indentation}  └─> Output: {result_str}")

        LogIndentation.decrease_indentation()

        return result

    return wrapper
