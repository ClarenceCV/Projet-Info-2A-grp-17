import pycountry_convert as pc
import worldcountrygroups


class Pays:
    """
    Classe pour les pays
    Attributes:
        code_iso (str): code unique pour identifier le pays.
        nom_pays (str): nom du pays

    """
    def __init__(
        self,
        code_iso: str,
        nom_pays: str
    ):
        """Constructor"""

        if not isinstance(code_iso, str):
            raise TypeError("code_iso should be a string")
        if not isinstance(nom_pays, str):
            raise TypeError("nom_pays should be a string")
        if not code_iso:
            raise ValueError("code_iso should not be empty")
        if not nom_pays:
            raise ValueError("nom_pays should not be empty")

        self.code_iso = code_iso
        self.nom_pays = nom_pays

    def __repr__(self):
        return f"Pays(code_iso={self.code_iso!r}, nom_pays={self.nom_pays!r})"

    def __eq__(self, other):
        if not isinstance(other, Pays):
            return NotImplemented
        return self.code_iso == other.code_iso and self.nom_pays == other.nom_pays

    def __hash__(self):
        return hash((self.code_iso, self.nom_pays))

    @staticmethod
    def continent_de(code_iso: str) -> str | None:
        """Renvoie le continent auquel appartient un pays, à partir de son code ISO.

        Args:
            code_iso (str): code ISO à 3 lettres du pays étudié (ex : 'FRA').

        Returns:
            str | None: code du continent (AF, AS, EU, NA, OC, SA)
                    ou None si le code est inconnu.
        """

        try:
            # ILOSTAT donne des codes à 3 lettres ('FRA'), pycountry_convert attend 2 lettres ('FR')
            code_alpha2 = pc.country_alpha3_to_country_alpha2(code_iso.upper())
            return pc.country_alpha2_to_continent_code(code_alpha2)
        except (KeyError, AttributeError):
            return None

    def continent(self) -> str | None:
        """Renvoie le continent auquel appartient le pays courant.

        Returns:
            str | None: code du continent (AF, AS, EU, NA, OC, SA)
                    ou None si le code est inconnu.
        """
        return Pays.continent_de(self.code_iso)

    @staticmethod
    def groupes_de(code_iso: str) -> list[str]:
        """Renvoie les groupes auxquels appartient un pays, à partir de son code ISO.

        Args:
            code_iso (str): code ISO du pays étudié (ex : 'FRA').

        Returns:
            list[str]: sigles des groupes auxquels appartient le pays (ex : ['EU', 'G7', ...]).
        """

        try:
            groupes = worldcountrygroups.search_groups(country=code_iso.upper())
            return [groupe.acronym or groupe.name for groupe in groupes]
        except (KeyError, ValueError, AttributeError):
            return []

    def groupes(self) -> list[str]:
        """Renvoie les groupes auxquels appartient le pays courant.

        Returns:
            list[str]: sigles des groupes auxquels appartient le pays.
        """
        return Pays.groupes_de(self.code_iso)


