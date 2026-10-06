# Récupère les données ILOSTAT et les enregistre dans la base (F1 + F2)
# Peut être relancé autant de fois que voulu : les observations existantes sont mises à jour, pas dupliquées
# Les indicateurs et pays importés se choisissent dans config_import.py
#
# Lancement (depuis backend/src, après utils.reset_database) :
#     uv run python -m fetcher.charger_donnees

import dotenv

from config_import import INDICATEURS
from fetcher.data_processing import DataProcessing
from utils.reset_database import ResetDatabase

if __name__ == "__main__":
    dotenv.load_dotenv(override=True)  # charge le .env avant la connexion

    DataProcessing().charger(INDICATEURS)

    print("\nContenu de la base :")
    ResetDatabase().afficher_tables()
