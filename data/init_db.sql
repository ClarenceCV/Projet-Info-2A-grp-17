-- Initialise la base de données LaborScope
-- Crée les tables correspondant à nos business objects (Pays, Indicateur, Profession, Observation)
-- ATTENTION : supprime tout le schéma existant (utilisé aussi par utils/reset_database.py)

DROP SCHEMA IF EXISTS laborscope CASCADE;
CREATE SCHEMA laborscope;


-- ---------------------------------------------------------------------
-- Pays (ou zone géographique : ILOSTAT fournit aussi des régions, ex : 'X01' = Monde)
-- ---------------------------------------------------------------------
CREATE TABLE laborscope.pays (
    id_pays   SERIAL       PRIMARY KEY,
    code_iso  VARCHAR(10)  NOT NULL UNIQUE,   -- 'FRA', 'DEU'... (colonne ref_area d'ILOSTAT)
    nom       VARCHAR(100) NOT NULL
);


-- ---------------------------------------------------------------------
-- Indicateur ILOSTAT
-- ---------------------------------------------------------------------
CREATE TABLE laborscope.indicateur (
    id_indicateur  SERIAL       PRIMARY KEY,
    code_ilostat   VARCHAR(50)  NOT NULL UNIQUE,  -- ex : 'EMP_5EMP_SEX_OC2_NB_Q'
    libelle        VARCHAR(255) NOT NULL,
    description    TEXT,
    unite          VARCHAR(50)  NOT NULL          -- 'milliers' ou '%'
);


-- ---------------------------------------------------------------------
-- Profession (classif1 de l'indicateur emploi par profession)
-- ---------------------------------------------------------------------
CREATE TABLE laborscope.profession (
    id_profession  SERIAL       PRIMARY KEY,
    libelle        VARCHAR(255) NOT NULL UNIQUE,
    niveau         INTEGER                        -- niveau dans la nomenclature (optionnel)
);


-- ---------------------------------------------------------------------
-- Observation : une ligne de données ILOSTAT
-- Une seule table pour tous les indicateurs :
--   - id_profession est rempli seulement pour les indicateurs par profession
--   - tranche_age est rempli seulement pour les indicateurs par âge
-- ---------------------------------------------------------------------
CREATE TABLE laborscope.observation (
    id_observation  SERIAL           PRIMARY KEY,
    id_indicateur   INTEGER          NOT NULL REFERENCES laborscope.indicateur(id_indicateur) ON DELETE CASCADE,
    id_pays         INTEGER          NOT NULL REFERENCES laborscope.pays(id_pays) ON DELETE CASCADE,
    id_profession   INTEGER          REFERENCES laborscope.profession(id_profession) ON DELETE CASCADE,
    tranche_age     VARCHAR(50),
    sexe            VARCHAR(50)      NOT NULL,
    source          VARCHAR(255)     NOT NULL,
    periode         CHAR(6)          NOT NULL CHECK (periode ~ '^[0-9]{4}Q[1-4]$'),  -- ex : '2024Q1'
    valeur          DOUBLE PRECISION NOT NULL,
    date_maj        TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Empêche les doublons quand le fetcher est relancé (récupération périodique).
    -- NULLS NOT DISTINCT (PostgreSQL >= 15) : deux NULL sont considérés égaux,
    -- sinon les lignes sans profession / sans tranche d'âge pourraient être dupliquées.
    CONSTRAINT uq_observation UNIQUE NULLS NOT DISTINCT
        (id_indicateur, id_pays, id_profession, tranche_age, sexe, source, periode)
);

-- Accélère les recherches les plus fréquentes (F3, F4, F5)
CREATE INDEX idx_observation_recherche
    ON laborscope.observation (id_indicateur, id_pays, periode);


-- ---------------------------------------------------------------------
-- Indicateurs suivis par l'application
-- ---------------------------------------------------------------------
INSERT INTO laborscope.indicateur (code_ilostat, libelle, description, unite) VALUES
    ('EMP_5EMP_SEX_OC2_NB_Q',
     'Emploi par sexe et profession',
     'Nombre de personnes en emploi, par sexe et grand groupe de profession (CITP-08), trimestriel',
     'milliers'),
    -- TODO : code à vérifier sur ILOSTAT (taux d'activité vs ratio emploi/population EMP_DWAP_...)
    ('EAP_DWAP_SEX_AGE_RT_Q',
     'Taux d''activité par sexe et âge',
     'Population active rapportée à la population en âge de travailler, par sexe et tranche d''âge, trimestriel',
     '%');
