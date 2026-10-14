
from buisness_object.pays.py import Pays
from dao.pays_dao import PaysDAO


class PaysService:
    """
    Service des pays
    """

    def lister(self) -> list[Pays]:
        """
        Liste les pays
        """
        return PaysDAO.lister()
