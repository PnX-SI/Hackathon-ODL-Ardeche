-- Importe les données éco-compteur :
--   - data/coords.json -> ardeche.ecocompteur_site
--   - data/ecocompteur.csv -> ardeche.ecocompteur_visit
--
-- Pré-requis : tables créées (modèles EcoCompteurSite et EcoCompteurVisit).

\set coords_path '../data/coords.json'
\set visits_path '../data/ecocompteur.csv'

BEGIN;

-- ------- Sites (coords.json) -------
CREATE TEMP TABLE tz_ecocompteur_coords_raw (raw jsonb);

\copy tz_ecocompteur_coords_raw(raw) FROM :'coords_path';

-- Extraire les entrées du JSON : clef = label attendu, lat/lon -> géométrie
WITH parsed AS (
    SELECT
        key AS label_key,
        (value ->> 'lat')::double precision AS lat,
        (value ->> 'lon')::double precision AS lon
    FROM tz_ecocompteur_coords_raw r,
         LATERAL jsonb_each(r.raw) AS t(key, value)
),
dedup AS (
    SELECT DISTINCT
        label_key AS nom,
        ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geometry(POINT, 4326) AS geom
    FROM parsed
    WHERE lat IS NOT NULL AND lon IS NOT NULL
)
INSERT INTO ardeche.ecocompteur_site (nom, geom)
SELECT d.nom, d.geom
FROM dedup d
WHERE NOT EXISTS (
    SELECT 1 FROM ardeche.ecocompteur_site s WHERE s.nom = d.nom
);

-- ------- Visites (ecocompteur.csv) -------
CREATE TEMP TABLE tz_ecocompteur_visit_raw (
    time text,
    count text,
    site text,
    month text
);

\copy tz_ecocompteur_visit_raw FROM :'visits_path' WITH (FORMAT csv, HEADER true, DELIMITER ',');

WITH site_lookup AS (
    SELECT id, nom FROM ardeche.ecocompteur_site
),
visits AS (
    SELECT
        sl.id AS site_id,
        to_date(v.month, 'YYYY-MM') AS date,
        COALESCE(NULLIF(v.count, '')::numeric, 0)::integer AS valeur
    FROM tz_ecocompteur_visit_raw v
    JOIN site_lookup sl ON sl.nom = v.site
    WHERE v.month IS NOT NULL
)
INSERT INTO ardeche.ecocompteur_visit (site_id, date, valeur)
SELECT site_id, date, valeur FROM visits;

COMMIT;
