"""Logique métier des pays : liste des pays disponibles (menus du frontend)."""

from business_object.pays import Pays
from dao.pays_dao import PaysDAO


class PaysService:
    """Service des pays."""

    def lister(self) -> list[Pays]:
        """
        Liste les pays présents dans la base.

        Returns:
            list[Pays]: les pays, triés par nom
        """
        return PaysDAO().lister()
