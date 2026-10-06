-- Initialise la base de données LaborScope (modèle en étoile)
--   - pays, indicateur : tables de dimensions (référentiels)
--   - observation      : table de faits (une ligne = une valeur ILOSTAT)
-- Les indicateurs ne sont pas insérés ici : l'import les crée à partir de la configuration Python.
-- ATTENTION : supprime tout le schéma existant (utilisé aussi par utils/reset_database.py)

DROP SCHEMA IF EXISTS laborscope CASCADE;
CREATE SCHEMA laborscope;
SET search_path TO laborscope;


-- ---------------------------------------------------------------------
-- Pays (ou zone géographique : ILOSTAT fournit aussi des régions, ex : 'X01' = Monde)
-- ---------------------------------------------------------------------
CREATE TABLE pays (
    code_iso  TEXT PRIMARY KEY,               -- 'FRA' (colonne ref_area d'ILOSTAT)
    nom       TEXT NOT NULL                   -- 'France' (colonne ref_area.label)
);


-- ---------------------------------------------------------------------
-- Indicateur ILOSTAT
-- ---------------------------------------------------------------------
CREATE TABLE indicateur (
    id            SERIAL PRIMARY KEY,
    code          TEXT NOT NULL UNIQUE,       -- id appelé dans l'API, ex : 'EMP_5EMP_SEX_OC2_NB_Q'
    libelle       TEXT NOT NULL,              -- nom lisible, ex : 'Emploi par sexe et profession'
    unite         TEXT NOT NULL,              -- 'milliers' ou '%'
    frequence     CHAR(1) NOT NULL,           -- 'Q' (trimestriel), 'A' (annuel), 'M' (mensuel)
    nom_classif1  TEXT                        -- ce que contient observation.classif1 : 'profession', 'tranche_age'
);


-- ---------------------------------------------------------------------
-- Observation : une valeur ILOSTAT pour un indicateur, un pays, une source,
-- une période, un sexe et une ventilation (classif1) donnés.
-- Les colonnes source, sexe et classif1 contiennent des libellés nettoyés par le parser.
-- ---------------------------------------------------------------------
CREATE TABLE observation (
    indicateur_id  INT  NOT NULL REFERENCES indicateur(id) ON DELETE CASCADE,
    code_iso       TEXT NOT NULL REFERENCES pays(code_iso),
    source         TEXT NOT NULL,                -- 'LFS - Employment Survey'
    periode        TEXT NOT NULL,                -- '2024Q4' : tri alphabétique = tri chronologique
    sexe           TEXT NOT NULL,                -- 'Total', 'Male', 'Female'
    classif1       TEXT NOT NULL DEFAULT '_NA',  -- '22 - Health professionals', '15-24' ('_NA' si absent)
    valeur         DOUBLE PRECISION NOT NULL,
    statut         TEXT,                         -- obs_status : NULL ou 'U' (valeur peu fiable)
    date_maj       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Identité d'une observation. Empêche les doublons quand l'import est relancé :
    -- une observation déjà présente voit sa valeur mise à jour (INSERT ... ON CONFLICT).
    PRIMARY KEY (indicateur_id, code_iso, source, periode, sexe, classif1)
);
