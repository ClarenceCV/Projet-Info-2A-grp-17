import dotenv
dotenv.load_dotenv()

from dao.observation_dao import ObservationDAO

def analyser_decalage():
    dao = ObservationDAO()
  
    # Chargement de deux indicateurs pour la France
    df_emploi = dao.lire("EMP_5WAP_SEX_AGE_RT_Q", ["FRA"])
    df_autre = dao.lire("EMP_5EMP_SEX_OC2_NB_Q", ["FRA"])

    print("=== Analyse du décalage temporel (Étape 0.c) ===")
    print(f"Taux d'emploi (RT)    : de {df_emploi['periode'].min()} à {df_emploi['periode'].max()}")
    print(f"Nombre d'employés (NB) : de {df_autre['periode'].min()} à {df_autre['periode'].max()}")

if __name__ == "__main__":
    analyser_decalage()