# Diagramme de classes UML - LaborScope

Premier jet du diagramme de classes, basé sur l'architecture en couches vue en
cours (vue / service / DAO / objet métier + `DBConnection` en Singleton) et sur
les fonctionnalités du sujet :

- **F1** Extraction périodique des données ILOSTAT
- **F2** Parsing (CSV/JSON) et stockage en base
- **F3** Analyse temporelle d'un indicateur
- **F4** Comparaison entre pays
- **F5** Comparaison multi-indicateurs
- **F6** Gestion des utilisateurs / droits
- **FO2 / FO3** Carte interactive et rapport PDF (optionnelles, en pointillés)

> GitHub affiche ce diagramme automatiquement (bloc ```mermaid```). Pour
> l'éditer, changez le code ci-dessous puis prévisualisez dans VS Code
> (extension "Markdown Preview Mermaid Support") ou directement sur GitHub.

```mermaid
classDiagram
    %% ===================== Couche Vue (API REST) =====================
    class IndicateurRouter {
        +get_indicateurs() list~Indicateur~
        +get_evolution(indicateur_id, pays_id, nb_periodes) JSON
    }
    class ComparaisonRouter {
        +compare_pays(indicateur_id, pays_ids, periode) JSON
        +compare_indicateurs(indicateur_ids, pays_id) JSON
    }
    class UtilisateurRouter {
        +login(email, mot_de_passe) Token
        +register(utilisateur) Utilisateur
    }
    class RapportRouter {
        <<optionnel FO3>>
        +generer_rapport(params) fichier_pdf
    }

    %% ===================== Couche Service =====================
    class ExtractionService {
        +extraire_donnees(indicateur_code, pays, periode) DataFrame
        +planifier_extraction() void
    }
    class ParsingService {
        +parser(contenu, format) list~Observation~
    }
    class AnalyseTemporelleService {
        +evolution_indicateur(indicateur, pays, nb_periodes) list~Observation~
    }
    class ComparaisonPaysService {
        +comparer_pays(indicateur, pays_ids, periode) dict
        +classement(indicateur, periode) list~Pays~
    }
    class ComparaisonIndicateursService {
        +comparer_indicateurs(indicateurs, pays) dict
    }
    class AuthService {
        +authentifier(email, mot_de_passe) Utilisateur
        +hash_mot_de_passe(mdp) str
        +verifier_droits(utilisateur, action) bool
    }
    class RapportService {
        <<optionnel FO3>>
        +generer_pdf(indicateurs, pays, periode) fichier
    }
    class CarteService {
        <<optionnel FO2>>
        +generer_carte(indicateur, periode) Carte
    }
    class IlostatApiClient {
        -base_url : str
        +recuperer_indicateur(code, pays, timefrom, timeto) str
    }

    %% ===================== Couche Objet métier =====================
    class Indicateur {
        -id : int
        -code : str
        -nom : str
        -description : str
        -unite : str
    }
    class Pays {
        -id : int
        -code_iso : str
        -nom : str
        -region : str
    }
    class Observation {
        -id : int
        -sexe : str
        -tranche_age : str
        -profession : str
        -periode : str
        -valeur : float
    }
    class Utilisateur {
        -id : int
        -nom : str
        -email : str
        -mot_de_passe_hash : str
        -role : Role
    }
    class Role {
        <<enumeration>>
        ADMIN
        USER
    }

    %% ===================== Couche DAO =====================
    class IndicateurDAO {
        +creer(indicateur) Indicateur
        +trouver_par_id(id) Indicateur
        +lister_tous() list~Indicateur~
    }
    class PaysDAO {
        +creer(pays) Pays
        +trouver_par_id(id) Pays
        +lister_tous() list~Pays~
    }
    class ObservationDAO {
        +creer(observation) Observation
        +creer_lot(observations) int
        +trouver_par_filtres(indicateur, pays, periode) list~Observation~
    }
    class UtilisateurDAO {
        +creer(utilisateur) Utilisateur
        +trouver_par_email(email) Utilisateur
    }
    class DBConnection {
        <<Singleton>>
        -connection
        +get_connection() connection
    }

    %% ===================== Relations Vue -> Service =====================
    IndicateurRouter --> AnalyseTemporelleService
    ComparaisonRouter --> ComparaisonPaysService
    ComparaisonRouter --> ComparaisonIndicateursService
    UtilisateurRouter --> AuthService
    RapportRouter --> RapportService

    %% ===================== Relations Service -> Service / externe ====
    ExtractionService --> IlostatApiClient
    ExtractionService --> ParsingService
    RapportService --> AnalyseTemporelleService
    RapportService --> ComparaisonPaysService
    CarteService --> ComparaisonPaysService

    %% ===================== Relations Service -> DAO =====================
    ExtractionService --> ObservationDAO
    ParsingService ..> Observation : crée
    AnalyseTemporelleService --> ObservationDAO
    ComparaisonPaysService --> ObservationDAO
    ComparaisonPaysService --> PaysDAO
    ComparaisonIndicateursService --> ObservationDAO
    AuthService --> UtilisateurDAO

    %% ===================== Relations DAO -> DBConnection =============
    IndicateurDAO --> DBConnection
    PaysDAO --> DBConnection
    ObservationDAO --> DBConnection
    UtilisateurDAO --> DBConnection

    %% ===================== Relations DAO -> Objet métier =============
    IndicateurDAO ..> Indicateur : crée
    PaysDAO ..> Pays : crée
    ObservationDAO ..> Observation : crée
    UtilisateurDAO ..> Utilisateur : crée

    %% ===================== Relations entre objets métier =============
    Observation "0..*" --> "1" Indicateur
    Observation "0..*" --> "1" Pays
    Utilisateur --> Role

    %% ===================== Styles par couche =====================
    classDef vue fill:#cde4ff,stroke:#3366cc,color:#000
    classDef service fill:#d4f5d4,stroke:#2e8b2e,color:#000
    classDef metier fill:#ffe6cc,stroke:#cc7a00,color:#000
    classDef dao fill:#e6d9f5,stroke:#7a3fa0,color:#000
    classDef externe fill:#f0f0f0,stroke:#888888,color:#000,stroke-dasharray: 3 3

    class IndicateurRouter,ComparaisonRouter,UtilisateurRouter,RapportRouter vue
    class ExtractionService,ParsingService,AnalyseTemporelleService,ComparaisonPaysService,ComparaisonIndicateursService,AuthService,RapportService,CarteService service
    class Indicateur,Pays,Observation,Utilisateur,Role metier
    class IndicateurDAO,PaysDAO,ObservationDAO,UtilisateurDAO,DBConnection dao
    class IlostatApiClient externe
```

## Correspondance fonctionnalités -> classes

| Fonctionnalité | Classes principales |
|---|---|
| F1 - Extraction ILOSTAT | `ExtractionService`, `IlostatApiClient`, `ObservationDAO` |
| F2 - Parsing et stockage | `ParsingService`, `Observation`, `ObservationDAO`, `DBConnection` |
| F3 - Analyse temporelle | `AnalyseTemporelleService`, `IndicateurRouter` |
| F4 - Comparaison pays | `ComparaisonPaysService`, `PaysDAO`, `ComparaisonRouter` |
| F5 - Comparaison multi-indicateurs | `ComparaisonIndicateursService` |
| F6 - Utilisateurs / droits | `Utilisateur`, `Role`, `AuthService`, `UtilisateurDAO`, `UtilisateurRouter` |
| FO2 - Carte interactive (optionnel) | `CarteService` |
| FO3 - Rapport PDF (optionnel) | `RapportService`, `RapportRouter` |

## Points à trancher en groupe

- **Base de données** : SQLite (simple, fichier local) ou PostgreSQL (plus proche de la prod, cf. cours DAO) ?
- **Frontend** : API seule, ou API + Streamlit/Dash comme le sujet le permet ? Si oui, ajouter une couche `Vue` correspondante en plus des routers REST.
- **Granularité des indicateurs** : un seul `Observation` générique suffit-il pour tous les indicateurs (emploi, chômage, participation...) ou faut-il des sous-classes par type d'indicateur ?
- **Authentification** : sessions ou JWT pour `AuthService` ?
