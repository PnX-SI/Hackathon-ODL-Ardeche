-- Crée les tables nécessaires aux imports quiet_zone et éco-compteur.
-- Inclut un correctif pour ajouter nom_valide si la table quiet_zone existe déjà.

BEGIN;

CREATE SCHEMA IF NOT EXISTS ardeche;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Table quiet_zone (zones de quiétude)
CREATE TABLE IF NOT EXISTS ardeche.quiet_zone (
    id SERIAL PRIMARY KEY,
    cd_nom INTEGER,
    nom_valide TEXT,
    geom geometry(MULTIPOLYGON, 4326)
);
ALTER TABLE ardeche.quiet_zone
    ADD COLUMN IF NOT EXISTS nom_valide TEXT;

-- Tables éco-compteur
CREATE TABLE IF NOT EXISTS ardeche.ecocompteur_site (
    id SERIAL PRIMARY KEY,
    nom TEXT,
    geom geometry(POINT, 4326)
);

CREATE TABLE IF NOT EXISTS ardeche.ecocompteur_visit (
    id SERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES ardeche.ecocompteur_site(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    valeur INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ecocompteur_visit_site_id ON ardeche.ecocompteur_visit(site_id);

COMMIT;
