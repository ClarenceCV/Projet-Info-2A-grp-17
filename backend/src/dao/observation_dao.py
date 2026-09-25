# Entrée : business object ; Sortie : sql (et inversement pour les lectures)

from psycopg2.extras import execute_values

from business_object.indicateur import Indicateur
from business_object.observation import Observation
from business_object.pays import Pays
from business_object.profession import Profession
from dao.db_connection import DBConnection

# Requête de base des lectures : une observation + son indicateur, son pays et sa profession
SELECT_OBSERVATION = """
    SELECT o.id_observation, o.sexe, o.tranche_age, o.periode, o.valeur,
           i.id_indicateur, i.code_ilostat, i.libelle AS libelle_indicateur, i.description, i.unite,
           p.code_iso, p.nom AS nom_pays,
           pr.id_profession, pr.libelle AS libelle_profession
    FROM laborscope.observation o
    JOIN laborscope.indicateur i USING (id_indicateur)
    JOIN laborscope.pays p USING (id_pays)
    LEFT JOIN laborscope.profession pr USING (id_profession)
"""


class ObservationDAO:
    """
    Accès aux observations dans la base de données (CRUD).
    Les pays et professions des observations sont créés automatiquement
    s'ils n'existent pas encore.
    """

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def creer(self, observation: Observation) -> bool:
        """
        Enregistre une seule observation (ex : ajout manuel par un administrateur).
        Si elle existe déjà (même indicateur, pays, sexe, âge, profession, période),
        sa valeur est mise à jour.

        Returns:
            bool: True si l'observation a été enregistrée
        """
        return self.creer_lot([observation]) == 1

    def creer_lot(self, observations: list[Observation]) -> int:
        """
        Enregistre une liste d'observations en une seule transaction :
            1. les pays rencontrés          (ignorés s'ils existent déjà)
            2. les professions rencontrées  (ignorées si elles existent déjà)
            3. les observations             (valeur mise à jour si elles existent déjà)
        Si une erreur survient, rien n'est enregistré (rollback).

        Returns:
            int: nombre d'observations insérées ou mises à jour
        """
        if not observations:
            return 0

        # set : chaque pays / profession n'est envoyé qu'une fois
        pays = {(o.pays.code_iso, o.pays.nom_pays) for o in observations}
        professions = {
            (o.profession.libelle_profession,) for o in observations if o.profession is not None
        }

        lignes_observation = [
            (
                o.indicateur.code_ilostat,
                o.pays.code_iso,
                o.profession.libelle_profession if o.profession is not None else None,
                o.tranche_age,
                o.sexe,
                o.periode,
                o.valeur,
            )
            for o in observations
        ]

        # with connection : commit si tout se passe bien, rollback en cas d'erreur
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                execute_values(
                    cursor,
                    "INSERT INTO laborscope.pays (code_iso, nom) VALUES %s "
                    "ON CONFLICT (code_iso) DO NOTHING;",
                    list(pays),
                )

                if professions:
                    execute_values(
                        cursor,
                        "INSERT INTO laborscope.profession (libelle) VALUES %s "
                        "ON CONFLICT (libelle) DO NOTHING;",
                        list(professions),
                    )

                # Les id (indicateur, pays, profession) sont retrouvés par sous-requêtes
                # à partir des codes / libellés : pas besoin de les connaître côté Python
                execute_values(
                    cursor,
                    "INSERT INTO laborscope.observation "
                    "(id_indicateur, id_pays, id_profession, tranche_age, sexe, periode, valeur) "
                    "VALUES %s "
                    "ON CONFLICT ON CONSTRAINT uq_observation "
                    "DO UPDATE SET valeur = EXCLUDED.valeur, date_maj = CURRENT_TIMESTAMP;",
                    lignes_observation,
                    template=(
                        "((SELECT id_indicateur FROM laborscope.indicateur "
                        "  WHERE code_ilostat = %s), "
                        " (SELECT id_pays FROM laborscope.pays WHERE code_iso = %s), "
                        " (SELECT id_profession FROM laborscope.profession WHERE libelle = %s), "
                        " %s, %s, %s, %s)"
                    ),
                    page_size=1000,
                )

        return len(lignes_observation)

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    def trouver_par_id(self, id_observation: int) -> Observation | None:
        """
        Cherche une observation par son identifiant.

        Returns:
            Observation | None: l'observation, ou None si elle n'existe pas
        """
        with DBConnection().connection.cursor() as cursor:
            cursor.execute(
                SELECT_OBSERVATION + " WHERE o.id_observation = %(id)s;",
                {"id": id_observation},
            )
            ligne = cursor.fetchone()

        return self._ligne_vers_observation(ligne) if ligne else None

    def trouver_par_filtres(
        self,
        code_indicateur: str,
        codes_pays: list[str] | None = None,
        sexe: str | None = None,
        profession: str | None = None,
        tranche_age: str | None = None,
        periode_debut: str | None = None,
        periode_fin: str | None = None,
    ) -> list[Observation]:
        """
        Cherche les observations d'un indicateur. Chaque filtre laissé à None est ignoré.
        ex : emploi des femmes en France et en Allemagne depuis 2024 :
            trouver_par_filtres("EMP_5EMP_SEX_OC2_NB_Q", ["FRA", "DEU"],
                                sexe="Female", periode_debut="2024Q1")

        params:
            code_indicateur: code ILOSTAT de l'indicateur (obligatoire)
            codes_pays: liste de codes ISO (ex : ["FRA", "DEU"])
            sexe: 'Total', 'Male', 'Female'
            profession: libellé exact de la profession
            tranche_age: ex '15-24'
            periode_debut, periode_fin: bornes incluses, format 'AAAAQn'

        Returns:
            list[Observation]: triées par pays puis par période
        """
        conditions = ["i.code_ilostat = %(code_indicateur)s"]
        if codes_pays:
            conditions.append("p.code_iso = ANY(%(codes_pays)s)")
        if sexe is not None:
            conditions.append("o.sexe = %(sexe)s")
        if profession is not None:
            conditions.append("pr.libelle = %(profession)s")
        if tranche_age is not None:
            conditions.append("o.tranche_age = %(tranche_age)s")
        if periode_debut is not None:
            conditions.append("o.periode >= %(periode_debut)s")
        if periode_fin is not None:
            conditions.append("o.periode <= %(periode_fin)s")

        requete = (
            SELECT_OBSERVATION
            + " WHERE " + " AND ".join(conditions)
            + " ORDER BY p.code_iso, o.periode;"
        )
        parametres = {
            "code_indicateur": code_indicateur,
            "codes_pays": codes_pays,
            "sexe": sexe,
            "profession": profession,
            "tranche_age": tranche_age,
            "periode_debut": periode_debut,
            "periode_fin": periode_fin,
        }

        with DBConnection().connection.cursor() as cursor:
            cursor.execute(requete, parametres)
            lignes = cursor.fetchall()

        return [self._ligne_vers_observation(ligne) for ligne in lignes]

    def derniere_periode(self, code_indicateur: str) -> str | None:
        """
        Période la plus récente disponible pour un indicateur (utile pour la fonctionnalité 4).

        Returns:
            str | None: ex '2026Q2', ou None si l'indicateur n'a aucune observation
        """
        with DBConnection().connection.cursor() as cursor:
            cursor.execute(
                "SELECT MAX(o.periode) AS derniere FROM laborscope.observation o "
                "JOIN laborscope.indicateur i USING (id_indicateur) "
                "WHERE i.code_ilostat = %(code)s;",
                {"code": code_indicateur},
            )
            return cursor.fetchone()["derniere"]

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def modifier_valeur(self, id_observation: int, nouvelle_valeur: float) -> bool:
        """
        Modifie la valeur d'une observation existante (action administrateur).

        Returns:
            bool: True si une observation a été modifiée, False si l'id n'existe pas
        """
        with DBConnection().connection as connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE laborscope.observation "
                    "SET valeur = %(valeur)s, date_maj = CURRENT_TIMESTAMP "
                    "WHERE id_observation = %(id)s;",
                    {"valeur": float(nouvelle_valeur), "id": id_observation},
                )
                return cursor.rowcount == 1

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def supprimer(self, id_observation: int) -> bool:
        """
        Supprime une observation (action administrateur).

        Returns:
            bool: True si une observation a été supprimée, False si l'id n'existe pas
        """
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM laborscope.observation WHERE id_observation = %(id)s;",
                    {"id": id_observation},
                )
                return cursor.rowcount == 1

    # ------------------------------------------------------------------
    # Conversion ligne SQL -> objet métier
    # ------------------------------------------------------------------
    @staticmethod
    def _ligne_vers_observation(ligne: dict) -> Observation:
        """
        Transforme une ligne renvoyée par SELECT_OBSERVATION en objet Observation.
        """
        profession = None
        if ligne["id_profession"] is not None:
            profession = Profession(
                libelle_profession=ligne["libelle_profession"],
                id_profession=ligne["id_profession"],
            )

        return Observation(
            indicateur=Indicateur(
                code_ilostat=ligne["code_ilostat"],
                libelle=ligne["libelle_indicateur"],
                unite=ligne["unite"],
                description=ligne["description"],
                id_indicateur=ligne["id_indicateur"],
            ),
            pays=Pays(code_iso=ligne["code_iso"], nom_pays=ligne["nom_pays"]),
            sexe=ligne["sexe"],
            periode=ligne["periode"],
            valeur=ligne["valeur"],
            profession=profession,
            tranche_age=ligne["tranche_age"],
            id_observation=ligne["id_observation"],
        )
