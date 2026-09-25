import math
import re

from business_object.indicateur import Indicateur
from business_object.pays import Pays
from business_object.profession import Profession


class Observation:
    """
    Une observation = une ligne de données ILOSTAT : la valeur d'un indicateur
    pour un pays, un trimestre et une ventilation (sexe, âge ou profession) donnés.

    Attributes:
        indicateur (Indicateur): indicateur mesuré
        pays (Pays): pays (ou zone) concerné
        sexe (str): ventilation par sexe ('Total', 'Male', 'Female'...)
        periode (str): trimestre au format 'AAAAQn' (ex : '2024Q1')
        valeur (float): valeur observée, dans l'unité de l'indicateur (milliers ou %)
        source (str): enquête d'origine (ex : 'LFS - Labour Force Survey')
        profession (Profession | None): seulement pour les indicateurs par profession
        tranche_age (str | None): seulement pour les indicateurs par âge (ex : '15-24')
        id_observation (int | None): identifiant en base, None tant que non enregistrée
    """

    FORMAT_PERIODE = re.compile(r"^\d{4}Q[1-4]$")

    def __init__(
        self,
        indicateur: Indicateur,
        pays: Pays,
        sexe: str,
        periode: str,
        valeur: float,
        source: str,
        profession: Profession | None = None,
        tranche_age: str | None = None,
        id_observation: int | None = None,
    ):
        """Constructor"""
        if not isinstance(indicateur, Indicateur):
            raise TypeError("indicateur should be an Indicateur")
        if not isinstance(pays, Pays):
            raise TypeError("pays should be a Pays")
        if not isinstance(sexe, str) or not sexe:
            raise ValueError("sexe should be a non empty string")
        if not isinstance(periode, str) or not self.FORMAT_PERIODE.match(periode):
            raise ValueError(f"periode should match 'AAAAQn' (ex : '2024Q1'), got {periode!r}")
        # bool est une sous-classe de int : on l'exclut explicitement
        if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
            raise TypeError("valeur should be a number")
        if math.isnan(valeur):
            raise ValueError("valeur should not be NaN")
        if not isinstance(source, str) or not source:
            raise ValueError("source should be a non empty string")
        if profession is not None and not isinstance(profession, Profession):
            raise TypeError("profession should be a Profession or None")
        if tranche_age is not None and not isinstance(tranche_age, str):
            raise TypeError("tranche_age should be a string or None")
        if id_observation is not None and not isinstance(id_observation, int):
            raise TypeError("id_observation should be an integer or None")

        self.indicateur = indicateur
        self.pays = pays
        self.sexe = sexe
        self.periode = periode
        self.valeur = float(valeur)
        self.source = source
        self.profession = profession
        self.tranche_age = tranche_age
        self.id_observation = id_observation

    @property
    def annee(self) -> int:
        """Année de la période (ex : 2024 pour '2024Q1')"""
        return int(self.periode[:4])

    @property
    def trimestre(self) -> int:
        """Numéro du trimestre de la période (ex : 1 pour '2024Q1')"""
        return int(self.periode[-1])

    def __str__(self):
        ventilation = self.sexe
        if self.tranche_age is not None:
            ventilation += f", {self.tranche_age}"
        if self.profession is not None:
            ventilation += f", {self.profession.libelle_profession}"
        return (
            f"{self.pays.nom_pays} - {self.indicateur.libelle} ({ventilation}) "
            f"{self.periode} : {self.valeur} {self.indicateur.unite}"
        )

    def __repr__(self):
        return (
            f"Observation(indicateur={self.indicateur.code_ilostat!r}, pays={self.pays.code_iso!r}, "
            f"sexe={self.sexe!r}, tranche_age={self.tranche_age!r}, "
            f"profession={self.profession.libelle_profession if self.profession else None!r}, "
            f"periode={self.periode!r}, valeur={self.valeur!r}, source={self.source!r})"
        )
