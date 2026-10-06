# Récupère les données ILOSTAT et les enregistre dans la base (F1 + F2)
# Peut être relancé autant de fois que voulu : les observations existantes sont mises à jour, pas dupliquées
#
# Lancement (depuis backend/src, après utils.reset_database) :
#     python -m charger_donnees

import dotenv

from business_object.indicateur import Indicateur
from dao.observation_dao import ObservationDAO
from fetcher.fetcher import construire_url, load_data
from fetcher.parser import mapper, nettoyer

# Indicateurs à charger (doivent aussi exister dans la table indicateur, c.f. data/init_db.sql)
INDICATEURS = [
    Indicateur("EMP_5EMP_SEX_OC2_NB_Q", "Emploi par sexe et profession", "milliers"),
    Indicateur("EAP_DWAP_SEX_AGE_RT_Q", "Taux d'activité par sexe et âge", "%"),
]

ANNEE_DEBUT = 2020


def charger_indicateur(indicateur):
    """
    Télécharge, nettoie et enregistre en base les données d'un indicateur.

    Returns:
        int: nombre d'observations enregistrées
    """
    print(f"\n[{indicateur.code_ilostat}] téléchargement...")
    brut = load_data(construire_url(indicateur.code_ilostat, ANNEE_DEBUT))
    print(f"  {len(brut)} lignes brutes reçues")

    propre = nettoyer(brut)
    print(f"  {len(propre)} lignes après nettoyage")

    observations = mapper(propre, indicateur)
    nb = ObservationDAO().creer_lot(observations)
    print(f"  {nb} observations enregistrées en base")
    return nb


if __name__ == "__main__":
    dotenv.load_dotenv(override=True)  # charge le .env avant la connexion

    total = 0
    for indicateur in INDICATEURS:
        try:
            total += charger_indicateur(indicateur)
        except Exception as e:
            # un indicateur en échec (ex : API indisponible) n'empêche pas de charger les autres
            print(f"  ERREUR : {e}")

    print(f"\nTerminé : {total} observations enregistrées au total.")
