# Logique métier liée aux indicateurs.
# Le controller appelle le service, le service appelle le DAO.

from business_object.indicateur import Indicateur
from dao.indicateur_dao import IndicateurDAO


class IndicateurService:
    """
    Service des indicateurs.
    """

    def lister(self) -> list[Indicateur]:
        """
        Liste les indicateurs disponibles dans la base.

        Returns:
            list[Indicateur]
        """
        return IndicateurDAO().lister()

    def trouver_par_code(self, code: str) -> Indicateur | None:
        """
        Cherche un indicateur par son code.

        Returns:
            Indicateur | None: l'indicateur, ou None s'il n'existe pas
        """
        return IndicateurDAO().trouver_par_code(code)
