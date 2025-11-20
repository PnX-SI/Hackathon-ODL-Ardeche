-- Importe les zones de quiétude depuis data/zq_rapace_4326.csv dans ardeche.quiet_zone
-- Le CSV est séparé par des ';' et contient une ligne d'en-tête.
-- Colonnes utilisées :
--   WKT   : géométrie (MULTIPOLYGON, projection 4326)
--   NOM   : nom de la zone de quiétude
--   cd_nom: identifiant d'espèce
\set csv_path '../data/zq_rapace_4326.csv'

BEGIN;

-- Table de staging pour parser proprement le CSV
CREATE TEMP TABLE tz_quiet_zone_import (
    wkt text,
    id_nom text,
    nom_valide text,
    cd_nom integer,
    espece text,
    sensib text,
    an_2012 text,
    an_2013 text,
    an_2014 text,
    an_2015 text,
    an_2016 text,
    an_2017 text,
    an_2018 text,
    an_2019 text,
    an_1974 text,
    an_1977 text,
    an_1992 text,
    an_1994 text,
    an_2004 text,
    an_2005 text,
    an_2006 text,
    an_2007 text,
    an_2009 text,
    an_2010 text,
    an_2011 text,
    an_2020 text,
    an_2021 text,
    an_2022 text,
    an_2023 text,
    an_2024 text,
    an_2025 text
);

COPY tz_quiet_zone_import
FROM :'csv_path'
WITH (FORMAT csv, DELIMITER ';', HEADER true, NULL '');

-- Insère dans le schéma ardeche.quiet_zone
INSERT INTO ardeche.quiet_zone (cd_nom, nom_valide, geom)
SELECT DISTINCT
    t.cd_nom,
    t.nom_valide,
    ST_SetSRID(ST_GeomFromText(t.wkt), 4326)::geometry(MULTIPOLYGON, 4326)
FROM tz_quiet_zone_import t
WHERE t.wkt IS NOT NULL
  AND t.cd_nom IS NOT NULL;

COMMIT;
