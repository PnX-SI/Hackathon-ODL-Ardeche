-- Création du schéma
CREATE SCHEMA IF NOT EXISTS ardeche;

-- Activation de l'extension PostGIS (si pas déjà activée)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Création de la table
CREATE TABLE ardeche.obs (
    id SERIAL PRIMARY KEY,
    cd_nom INTEGER,
    nom_valide TEXT,
    geometry geometry(Point, 4326),  -- 4326 par défaut, adapte si besoin
    date_debut DATE,
    date_fin DATE,
    behaviour TEXT,
    species_age TEXT,
    niveau_sensibilite TEXT
);

-- Table "trace"
CREATE TABLE ardeche.trace (
    id SERIAL PRIMARY KEY,
    tack_id INTEGER,
    date_start DATE,
    date_end DATE,
    geom geometry(MultiPolygon, 4326)  -- SRID ajustable si besoin
);

-- Table "quiet_zone"
CREATE TABLE ardeche.quiet_zone (
    id SERIAL PRIMARY KEY,
    cd_nom INTEGER,
    geom geometry(MultiPolygon, 4326)  -- SRID ajustable si nécessaire
);