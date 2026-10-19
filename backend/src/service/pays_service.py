
from business_object.pays import Pays
from dao.pays_dao import PaysDAO


class PaysService:
    """
    Service des pays
    """

    def lister(self) -> list[Pays]:
        """
        Liste les pays
        """
        return PaysDAO.lister(self)
