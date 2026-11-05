# Diagramme de classes - Objets métier (business_object)

Diagramme limité au dossier [backend/src/business_object/](../../backend/src/business_object/),
fidèle au code actuel.

```mermaid
classDiagram
    direction LR

    class Indicateur {
        <<dataclass frozen>>
        +code : str
        +libelle : str
        +unite : str
        +frequence : str
        +nom_classif1 : str | None = None
        +__post_init__() None
        +__str__() str
    }

    class Pays {
        +code_iso : str
        +nom_pays : str
        +__init__(code_iso, nom_pays)
        +__repr__() str
        +__eq__(other) bool
        +__hash__() int
        +continent_de(code_iso)$ str | None
        +continent() str | None
        +groupes_de(code_iso)$ list~str~
        +groupes() list~str~
    }

    class Selection {
        <<dataclass frozen>>
        +indicateur : str
        +pays : str
        +classif1 : str
        +sexe : str = "Total"
    }

    class Utilisateur {
        <<dataclass>>
        +pseudo : str
        +role : str = "utilisateur"
        +id : int | None = None
        +date_creation : datetime | None = None
        +__post_init__() None
        +est_admin : bool  «property»
        +__str__() str
    }

    class ActionJournal {
        <<dataclass>>
        +action : str
        +pseudo : str | None = None
        +detail : str | None = None
        +utilisateur_id : int | None = None
        +id : int | None = None
        +date : datetime | None = None
        +__post_init__() None
    }

    class ROLES {
        <<constante>>
        utilisateur
        admin
    }

    class ACTIONS {
        <<constante>>
        connexion
        echec_connexion
        deconnexion
        creation_compte
        suppression_compte
        import_donnees
        modification_donnee
        suppression_donnee
    }

    %% Relations (par identifiant, pas par objet)
    Selection "0..*" ..> "1" Indicateur : indicateur = code
    Selection "0..*" ..> "1" Pays : pays = code_iso
    ActionJournal "0..*" ..> "0..1" Utilisateur : utilisateur_id = id
    Utilisateur ..> ROLES : role ∈
    ActionJournal ..> ACTIONS : action ∈
```

## Lecture du diagramme

- **Flèches en pointillés** : aucun objet métier ne contient un autre objet métier.
  Les liens se font **par identifiant** (une chaîne ou un entier), par exemple
  `Selection.pays` contient `"FRA"`, pas un objet `Pays`.
- `ActionJournal → Utilisateur` est en `0..1` : `utilisateur_id` passe à `None`
  quand le compte est supprimé (le `pseudo` est copié pour garder la trace).
- `ROLES` et `ACTIONS` ne sont pas des classes mais des constantes de module ;
  elles sont représentées pour montrer les valeurs vérifiées dans `__post_init__`.
- `$` = méthode statique (`@staticmethod`).
