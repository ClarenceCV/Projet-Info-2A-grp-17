# Point d'entrée du webservice FastAPI LaborScope.
#
# Lancement (depuis backend/src) :
#     uv run python main.py
# Puis ouvrir la documentation interactive : <url du service>/docs
# (sur Onyxia : Mes services > VSCode > Ouvrir > lien du port 5000)

import os
import dotenv
import uvicorn

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from controller import indicateur_controller, observation_controller, evolution_controller
from controller import pays_controller
from controller import multi_indicateurs_controller
from controller import login_controller, utilisateur_controller

# charge le .env (connexion à la base, host et port du webservice)
dotenv.load_dotenv(override=True)

app = FastAPI(title="LaborScope", description="Analyse du marché du travail mondial (ILOSTAT)")

# chaque controller regroupe les endpoints d'un thème, sous un préfixe commun
app.include_router(indicateur_controller.router, prefix="/indicateurs", tags=["Indicateurs"])
app.include_router(observation_controller.router, prefix="/observations", tags=["Observations"])
app.include_router(evolution_controller.router, prefix="/analyses", tags=["Analyses"])
app.include_router(pays_controller.router, prefix="/pays", tags=["Pays"])
app.include_router(multi_indicateurs_controller.router, prefix="/analyses", tags=["Analyses"])
app.include_router(login_controller.router, tags=["Connexion"])
app.include_router(utilisateur_controller.router, prefix="/utilisateurs", tags=["Utilisateurs"])


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """Redirige la page d'accueil vers la documentation de l'API"""
    return RedirectResponse(url="/docs")


@app.get("/hello/{name}", tags=["Test"])
async def hello_name(name: str):
    """Renvoie un message de bienvenue (pour tester que le webservice fonctionne)"""
    return {"message": f"Hello {name}"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("UVICORN_HOST", "0.0.0.0"),  # 0.0.0.0 sur Onyxia pour être joignable
        port=int(os.getenv("UVICORN_PORT", "5000")),
    )