# DataProcessing regroupe tout l'import des données ILOSTAT (F1 + F2) :
#   1. fetch_data : télécharger un indicateur depuis l'API ILOSTAT (DataFrame brut)
#   2. parse_data : nettoyer le DataFrame brut (DataFrame propre, prêt pour la base)
#   3. save_data  : enregistrer le DataFrame propre dans la base (via les DAO)
#   charger      : enchaîner 1, 2 et 3 pour une liste d'indicateurs
# Le téléchargement réutilise les fonctions de fetcher.py (construire_url, load_data).
# Les requêtes SQL restent dans le dossier dao.

import pandas as pd

from business_object.indicateur import Indicateur
from config_import import ANNEE_DEBUT, PAYS_SUIVIS
from dao.indicateur_dao import IndicateurDAO
from dao.observation_dao import ObservationDAO
from dao.pays_dao import PaysDAO
from fetcher.fetcher import URL_ILOSTAT, construire_url, load_data
from fetcher.parser import retirer_prefixe

# Colonnes du CSV ILOSTAT à garder -> nom dans le DataFrame propre
RENOMMAGE = {
    "ref_area": "code_iso",
    "ref_area.label": "nom_pays",
    "source.label": "source",
    "time": "periode",
    "sex.label": "sexe",
    "classif1.label": "classif1",
    "obs_value": "valeur",
    "obs_status": "statut",
}

# Colonnes du DataFrame propre (= colonnes de la table observation, + nom_pays pour la table pays)
COLONNES = ["code_iso", "nom_pays", "source", "periode", "sexe", "classif1", "valeur", "statut"]

# Colonnes qui identifient une observation (= clé primaire de la table observation, sans l'indicateur)
CLE = ["code_iso", "source", "periode", "sexe", "classif1"]


class DataProcessing:
    """
    Récupère, nettoie et enregistre en base les données des indicateurs ILOSTAT.

    Attributes:
        url_API (str): adresse de l'API ILOSTAT (celle utilisée par construire_url)
    """

    def __init__(self):
        """Constructor"""
        self.url_API = URL_ILOSTAT

    def fetch_data(self, indicator: str) -> pd.DataFrame:
        """
        Télécharge un indicateur pour les pays suivis (c.f. config_import.py),
        un appel à l'API par pays.

        params:
            indicator: code de l'indicateur, ex : 'EMP_5EMP_SEX_OC2_NB_Q'

        Returns:
            pd.DataFrame: données brutes de tous les pays réunies (colonnes de l'API ILOSTAT)
        """
        morceaux = []
        for code_iso in PAYS_SUIVIS:
            # url de fetcher.py + filtre sur un seul pays
            url = construire_url(indicator, ANNEE_DEBUT) + f"&ref_area={code_iso}"
            df_pays = load_data(url)
            print(f"  {indicator} - {code_iso} : {len(df_pays)} lignes")
            if not df_pays.empty:  # pays sans données : on passe au suivant
                morceaux.append(df_pays)

        if not morceaux:
            return pd.DataFrame()
        return pd.concat(morceaux, ignore_index=True)

    def parse_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforme le DataFrame brut en DataFrame propre.

        Étapes :
            1. sélection et renommage des colonnes utiles
            2. suppression des lignes sans valeur
            3. retrait des préfixes ILOSTAT ('Age (Youth, adults): 15-24' -> '15-24')
            4. suppression des doublons sur la clé (sinon l'insertion en base échoue)

        params:
            df: DataFrame brut issu de fetch_data()

        Returns:
            pd.DataFrame: colonnes code_iso, nom_pays, source, periode, sexe, classif1, valeur, statut
        """
        if df.empty:
            return pd.DataFrame(columns=COLONNES)

        # 1. sélection PUIS renommage (dans l'autre sens, 'source.label' renommé en 'source'
        #    entrerait en conflit avec la colonne 'source' du CSV, qui contient le code)
        #    classif1 et obs_status peuvent être absents selon l'indicateur
        df = df.copy()
        if "classif1.label" not in df.columns:
            df["classif1.label"] = "_NA"
        if "obs_status" not in df.columns:
            df["obs_status"] = None
        df = df[list(RENOMMAGE)].rename(columns=RENOMMAGE)

        # 2. valeur convertie en nombre (les textes invalides deviennent NaN), puis lignes sans valeur supprimées
        df["valeur"] = pd.to_numeric(df["valeur"], errors="coerce")
        df = df.dropna(subset=["valeur"])

        # 3. libellés nettoyés ; dimension absente -> '_NA'
        df["sexe"] = df["sexe"].map(retirer_prefixe)
        df["classif1"] = df["classif1"].map(retirer_prefixe).fillna("_NA")
        # statut : NaN (valeur fiable) -> None, pour avoir NULL en base
        df["statut"] = df["statut"].astype(object).where(df["statut"].notna(), None)

        # 4. doublons : deux sources différentes peuvent avoir le même libellé
        nb_doublons = df.duplicated(CLE).sum()
        if nb_doublons:
            print(f"  Attention : {nb_doublons} doublons sur la clé, seule la première ligne est gardée")
            df = df.drop_duplicates(CLE, keep="first")

        return df.reset_index(drop=True)

    def save_data(self, indicateur: Indicateur, df: pd.DataFrame) -> int:
        """
        Enregistre en base un indicateur et ses observations, dans cet ordre :
            1. l'indicateur (pour obtenir son id)
            2. les pays (la table observation fait référence à la table pays)
            3. les observations

        params:
            indicateur: indicateur auquel appartiennent les données
            df: DataFrame propre issu de parse_data()

        Returns:
            int: nombre d'observations enregistrées
        """
        indicateur_id = IndicateurDAO().enregistrer(indicateur)
        PaysDAO().enregistrer(df[["code_iso", "nom_pays"]])
        return ObservationDAO().enregistrer(indicateur_id, df)

    def charger(self, indicateurs: list[Indicateur]) -> int:
        """
        Télécharge, nettoie et enregistre en base chaque indicateur.
        Un indicateur en échec (ex : API indisponible) n'empêche pas de charger les autres.
        Peut être relancé autant de fois que voulu : les observations existantes
        sont mises à jour, pas dupliquées.

        params:
            indicateurs: indicateurs à charger (c.f. config_import.INDICATEURS)

        Returns:
            int: nombre total d'observations enregistrées
        """
        total = 0
        for indicateur in indicateurs:
            print(f"\n[{indicateur.code}] {indicateur}")
            try:
                brut = self.fetch_data(indicateur.code)
                propre = self.parse_data(brut)
                print(f"  {len(brut)} lignes brutes -> {len(propre)} lignes propres")
                nb = self.save_data(indicateur, propre)
                print(f"  {nb} observations enregistrées en base")
                total += nb
            except Exception as e:
                print(f"  ERREUR : {e}")

        print(f"\nTerminé : {total} observations enregistrées au total.")
        return total
