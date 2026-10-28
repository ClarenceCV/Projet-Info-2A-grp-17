# Hachage des mots de passe avec bcrypt (sujet : « Sécurité : bcrypt, sessions/tokens »)
# (inspiré du template ENSAI : backend/src/utils/security.py, qui utilise SHA-256)
#
# On ne stocke JAMAIS un mot de passe : seulement son hash, calculé à sens unique.
# Pour vérifier une connexion, on recalcule et on compare avec bcrypt.checkpw.

import bcrypt


def hacher_mdp(mot_de_passe: str) -> str:
    """
    Calcule le hash bcrypt d'un mot de passe, avec un sel aléatoire.
    Le même mot de passe donne un hash différent à chaque appel.

    params:
        mot_de_passe: mot de passe en clair (72 octets maximum, limite de bcrypt)

    Returns:
        str: hash de 60 caractères, ex : '$2b$12$jBH8ATehxGBD...' (contient aussi le sel)
    """
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verifier_mdp(mot_de_passe: str, mdp_hash: str) -> bool:
    """
    Vérifie qu'un mot de passe correspond à un hash enregistré.

    params:
        mot_de_passe: mot de passe saisi, en clair
        mdp_hash: hash lu dans la base

    Returns:
        bool: True si le mot de passe est le bon
    """
    try:
        return bcrypt.checkpw(mot_de_passe.encode("utf-8"), mdp_hash.encode("utf-8"))
    except ValueError:  # mot de passe trop long (> 72 octets) ou hash mal formé
        return False
