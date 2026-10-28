# Client HTTP du backend : TOUS les appels du frontend vers l'API FastAPI passent par ici.
# (repris du template)
#
# Utilisation dans une page :
#     from utils.api_client import api_client
#
#     reponse = api_client.get("/indicateurs")
#     if reponse["status_code"] == 200:
#         indicateurs = reponse["data"]

import os

import dotenv
import requests
import streamlit as st

# charge le .env (cherché en remontant les dossiers depuis ce fichier : on trouve celui de la racine)
dotenv.load_dotenv()

# Adresse du backend. Streamlit et l'API tournent sur la même machine (le service VSCode Onyxia pour nous) :
# c'est le serveur Streamlit, et non le navigateur, qui appelle l'API, donc localhost fonctionne (on fait pas une vrai app en ligne).
API_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
DEFAULT_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT") or 10)  # 10 secondes d.v. si ce n'est pas rensigné dans le .env


class APIClient:
    """
    Client pour envoyer des requêtes HTTP au backend, avec le token de connexion.

    Attributes:
        base_url (str): adresse du backend, ex : 'http://localhost:5000'
        timeout (int): délai d'attente maximum d'une réponse, en secondes
        session (requests.Session): connexion réutilisée d'une requête à l'autre (plus rapide)
    """

    def __init__(self, base_url: str, timeout: int = DEFAULT_TIMEOUT):
        """Constructor"""
        self.base_url = base_url.rstrip("/")  # évite les '//' dans les URL
        self.timeout = timeout
        self.session = requests.Session()

    def _get_headers(self) -> dict:
        """
        En-têtes HTTP à envoyer : le token de l'utilisateur connecté, s'il y en a un.

        Returns:
            dict: ex {'X-Auth-Token': 'abc...'} ou {} si personne n'est connecté
        """
        headers = {}
        token = st.session_state.get("token")  # rempli à la connexion (page de connexion)
        if token:
            headers["X-Auth-Token"] = token  # même nom que dans backend/src/controller/auth.py
        return headers

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """
        Méthode commune à toutes les requêtes (GET, POST, PUT, DELETE).
        Ne lève jamais d'exception : les erreurs sont renvoyées dans le dictionnaire.

        params:
            method: 'GET', 'POST', 'PUT' ou 'DELETE'
            path: chemin de l'endpoint, ex : '/indicateurs'
            **kwargs: autres arguments de requests (params, json, timeout...)

        Returns:
            dict: {'status_code': code HTTP (0 si le backend est injoignable),
                   'data': réponse JSON décodée (ou texte / message d'erreur)}
        """
        url = f"{self.base_url}{path}"

        # on ajoute le token aux éventuels en-têtes déjà fournis
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())
        timeout = kwargs.pop("timeout", self.timeout)

        try:
            response = self.session.request(
                method=method, url=url, timeout=timeout, headers=headers, **kwargs
            )
            try:
                data = response.json()
            except ValueError:  # la réponse n'est pas du JSON (ex : un fichier PDF)
                data = response.text
            return {"status_code": response.status_code, "data": data}

        except requests.exceptions.Timeout:
            return {"status_code": 0, "data": "Le backend ne répond pas (délai dépassé)."}
        except requests.exceptions.ConnectionError:
            return {"status_code": 0, "data": f"Impossible de joindre le backend ({self.base_url}). Est-il lancé ?"}
        except requests.exceptions.RequestException as e:
            return {"status_code": 0, "data": str(e)}

    def get(self, path: str, params: dict | None = None, **kwargs) -> dict:
        """Envoie une requête GET (lecture). params : paramètres d'URL, ex {'pays': ['FRA', 'ESP']}"""
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, json=None, **kwargs) -> dict:
        """Envoie une requête POST (création / action). json : corps de la requête"""
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path: str, json=None, **kwargs) -> dict:
        """Envoie une requête PUT (modification). json : corps de la requête"""
        return self._request("PUT", path, json=json, **kwargs)

    def delete(self, path: str, json=None, **kwargs) -> dict:
        """Envoie une requête DELETE (suppression)."""
        return self._request("DELETE", path, json=json, **kwargs)


# Instance unique, importée par toutes les pages
api_client = APIClient(API_URL)
