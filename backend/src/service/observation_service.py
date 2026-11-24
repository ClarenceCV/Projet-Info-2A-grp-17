"""
Logique métier liée aux observations (plus tard : F3 évolution,
F4 comparaison pays, F5 multi-indicateurs).
Le controller appelle le service, le service appelle le DAO.
"""

import pandas as pd

from dao.observation_dao import ObservationDAO
from schema.observation_model import CleObservationModel


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

        Args:
            code_indicateur (str): code de l'indicateur (obligatoire)
            pays (list[str] | None): codes ISO, ex : ['FRA', 'DEU'] (None = tous les pays)
            periode_min (str | None): première période incluse, ex : '2024Q1'
            periode_max (str | None): dernière période incluse, ex : '2024Q4'
            sexe (str | None): 'Total', 'Male' ou 'Female'
            classif1 (str | None): profession ou tranche d'âge, ex : '15+'
            limite (int | None): nombre maximum de lignes renvoyées (None = toutes)

        Returns:
            pd.DataFrame: une ligne par observation
        """
        return ObservationDAO().lire(
            code_indicateur, pays, periode_min, periode_max, sexe, classif1, limite
        )

    def lister_classif1(self, code_indicateur: str) -> pd.DataFrame:
        """
        Liste toutes les modalités distinctes d'un indicateur contenues dans
        les observations de la base (tranche d'âge / profession).

        Args:
            code_indicateur (str): (obligatoire) code de l'indicateur étudier
        Returns:
            DataFrame avec toutes les modalités.
        """
        return ObservationDAO().lister_classif1(code_indicateur)

    def modifier(self, cle: CleObservationModel, nouvelle_valeur: float) -> bool:
        """
        Modifie la valeur d'une observation à partir de sa clé primaire.

        Args:
            cle (CleObservationModel): tuple contenant les 6 éléments de la clé primaire.
            nouvelle_valeur (float): nouvelle valeur de l'observation.

        Returns:
            bool: True si la modification a réussi, False sinon.
        """
        return ObservationDAO().modifier(cle, nouvelle_valeur)

    def supprimer(self, cle: CleObservationModel) -> bool:
        """
        Supprime une observation à partir de sa clé primaire.

        Args:
            cle (CleObservationModel): clé primaire de l'observation (indicateur, pays, source,
                période, sexe, classif1)

        Returns:
            bool: True si la suppression a réussi, False sinon.
        """
        return ObservationDAO().supprimer(cle)
