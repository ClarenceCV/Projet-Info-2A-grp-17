# Logique métier liée aux observations (plus tard : F3 évolution, F4 comparaison pays, F5 multi-indicateurs).
# Le controller appelle le service, le service appelle le DAO.

import pandas as pd
from dao.observation_dao import ObservationDAO


class ObservationService:
    """
    Service des observations.
    """
    def lister(
        self,
        code_indicateur: str,
        pays: list[str] | None = None,
        periode_min: str | None = None,
        periode_max: str | None = None,
        sexe: str | None = None,
        classif1: str | None = None,
        limite: int | None = None,
    ) -> pd.DataFrame:
        """
        Liste les observations d'un indicateur selon les filtres donnés
        (c.f. ObservationDAO.lire pour le détail des filtres).

        Returns:
            pd.DataFrame: une ligne par observation
        """
        return ObservationDAO().lire(
            code_indicateur, pays, periode_min, periode_max, sexe, classif1, limite
        )

    def lister_classif1(self, code_indicateur: str) -> pd.DataFrame:
        """
        Liste toutes les modalités disctinctes d'un indictauyr contenues dans 
        les observations de la base (tranche d'age / profession).

        Params:
            code_indicateur: (obligatoire) code de l'indicateur étudier
        Return:
            DataFrame avec toutes les modalités.
        """
        return ObservationDAO().lister_classif1(code_indicateur)
