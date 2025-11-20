import json
import time

from flask import Blueprint, jsonify, request

from backend.models.obs import Obs
from backend.models.quiet_zone import QuietZone
from backend.models.trace import Trace, Grille
from backend.utils.env import db
from sqlalchemy import func, and_, or_, text, case
from datetime import datetime

routes = Blueprint("ardeche", __name__, url_prefix="/api")


@routes.route("/ping", methods=["GET"])
def ping():
    return jsonify(status="ok", message="Ardeche API is alive")


@routes.route("/species", methods=["GET"])
def list_quiet_zone_species():
    # Récupère les espèces depuis quiet_zone et obs, et fusionne en liste unique
    quiet_zone_rows = QuietZone.query.with_entities(
        QuietZone.cd_nom, QuietZone.nom_valide
    ).all()
    obs_rows = Obs.query.with_entities(Obs.cd_nom, Obs.nom_valide).all()

    species_map = {}

    for row in (*quiet_zone_rows, *obs_rows):
        if row.cd_nom is None:
            continue
        if row.cd_nom not in species_map:
            species_map[row.cd_nom] = {
                "cd_nom": row.cd_nom,
                "nom_valide": row.nom_valide,
            }
        elif not species_map[row.cd_nom]["nom_valide"] and row.nom_valide:
            species_map[row.cd_nom]["nom_valide"] = row.nom_valide

    species = sorted(
        species_map.values(),
        key=lambda item: (item["cd_nom"], item["nom_valide"] or ""),
    )

    return jsonify(species=species)


@routes.route("/grid", methods=["GET"])
def obs_grid():
    # Agrège les observations par maille (grille) et retourne une FeatureCollection
    cell_size = float(request.args.get("cell_size", "0.01"))
    cd_nom_params = request.args.getlist("cd_nom")
    if len(cd_nom_params) == 1 and "," in cd_nom_params[0]:
        cd_nom_params = [part for part in cd_nom_params[0].split(",") if part]

    cd_nom_values = []
    for value in cd_nom_params:
        try:
            cd_nom_values.append(int(value))
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "Paramètre cd_nom invalide",
                        "detail": f"'{value}' n'est pas un entier",
                    }
                ),
                400,
            )

    snapped_geom = func.ST_SnapToGrid(Obs.geom, cell_size)
    query = db.session.query(
        func.ST_AsGeoJSON(snapped_geom).label("geom_geojson"),
        func.count().label("count"),
    ).filter(Obs.geom.isnot(None))

    if cd_nom_values:
        query = query.filter(Obs.cd_nom.in_(cd_nom_values))

    results = (
        query.group_by(snapped_geom).all()
    )

    features = [
        {
            "type": "Feature",
            "geometry": json.loads(row.geom_geojson),
            "properties": {"count": row.count},
        }
        for row in results
    ]

    return jsonify({"type": "FeatureCollection", "features": features})

@routes.route("/analyse", methods=["GET"])
def analyse():
    """
    Analyse les traces par grille en opération spatiale.
    Retourne un GeoJSON avec le nombre de passages par grille.
    Filtre sur date_start entre date-min et date-max.
    """
    # Récupération des paramètres de date
    date_min_str = request.args.get("date-min")
    date_max_str = request.args.get("date-max")
    
    if not date_min_str or not date_max_str:
        return (
            jsonify(
                {
                    "error": "Paramètres manquants",
                    "detail": "Les paramètres 'date-min' et 'date-max' sont requis (format: YYYY-MM-DD)",
                }
            ),
            400,
        )
    
    # Conversion des dates
    try:
        date_min = datetime.strptime(date_min_str, "%Y-%m-%d").date()
        date_max = datetime.strptime(date_max_str, "%Y-%m-%d").date()
    except ValueError:
        return (
            jsonify(
                {
                    "error": "Format de date invalide",
                    "detail": "Les dates doivent être au format YYYY-MM-DD",
                }
            ),
            400,
        )
    
    # Requête optimisée : utilise && (bounding box) avant ST_Intersects pour performance
    # Filtre d'abord les traces par date, puis fait le LEFT JOIN
    # Utilise une sous-requête pour filtrer les traces avant la jointure spatiale
    traces_filtered = db.session.query(Trace).filter(
        Trace.date_start >= date_min,
        Trace.date_start <= date_max
    ).subquery()
    
    TraceFiltered = db.aliased(Trace, traces_filtered)
    
    # Utilisation de l'opérateur && (bounding box) avant ST_Intersects pour optimiser
    # L'opérateur && vérifie rapidement si les bounding boxes se chevauchent
    query = (
        db.session.query(
            Grille.id,
            func.ST_AsGeoJSON(Grille.geom).label("geom_geojson"),
            func.count(TraceFiltered.id).label("nb_passages"),
        )
        .outerjoin(
            TraceFiltered,
            and_(
                Grille.geom.op('&&')(TraceFiltered.geom),  # Bounding box check (rapide)
                func.ST_Intersects(Grille.geom, TraceFiltered.geom)  # Intersection précise
            )
        )
        .filter(Grille.geom.isnot(None))
        .group_by(Grille.id, Grille.geom)
    )
    
    results = query.all()
    
    # Construction du GeoJSON FeatureCollection
    features = [
        {
            "type": "Feature",
            "geometry": json.loads(row.geom_geojson) if row.geom_geojson else None,
            "properties": {
                "id": row.id,
                "nb_passages": row.nb_passages or 0,
            },
        }
        for row in results
    ]
    
    return jsonify({"type": "FeatureCollection", "features": features})


@routes.route("/zones-sensibles", methods=["GET"])
def zones_sensibles():
    """
    Filtre les observations, crée un buffer de 50m et détermine si elles sont en zone sensible.
    Une zone est sensible si le buffer intersecte une grille avec nb_passages > 50.
    """
    # Récupération des paramètres
    date_min_str = request.args.get("date-min")
    date_max_str = request.args.get("date-max")
    cd_nom_str = request.args.get("cd_nom")
    
    if not date_min_str or not date_max_str:
        return (
            jsonify(
                {
                    "error": "Paramètres manquants",
                    "detail": "Les paramètres 'date-min' et 'date-max' sont requis (format: YYYY-MM-DD)",
                }
            ),
            400,
        )
    
    if not cd_nom_str:
        return (
            jsonify(
                {
                    "error": "Paramètre manquant",
                    "detail": "Le paramètre 'cd_nom' est requis",
                }
            ),
            400,
        )
    
    # Conversion des dates
    try:
        date_min = datetime.strptime(date_min_str, "%Y-%m-%d").date()
        date_max = datetime.strptime(date_max_str, "%Y-%m-%d").date()
    except ValueError:
        return (
            jsonify(
                {
                    "error": "Format de date invalide",
                    "detail": "Les dates doivent être au format YYYY-MM-DD",
                }
            ),
            400,
        )
    
    # Conversion de cd_nom
    try:
        cd_nom = int(cd_nom_str)
    except ValueError:
        return (
            jsonify(
                {
                    "error": "Paramètre cd_nom invalide",
                    "detail": f"'{cd_nom_str}' n'est pas un entier",
                }
            ),
            400,
        )
    
    start_time = time.time()
    print(f"[zones-sensibles] Début - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    # Sous-requête pour obtenir les grilles avec leur nb_passages (même logique que /analyse)
    print(f"[zones-sensibles] Étape 1: Filtrage des traces...")
    step_time = time.time()
    traces_filtered = db.session.query(Trace).filter(
        Trace.date_start >= date_min,
        Trace.date_start <= date_max
    ).subquery()
    
    TraceFiltered = db.aliased(Trace, traces_filtered)
    print(f"[zones-sensibles] Étape 1 terminée: {time.time() - step_time:.2f}s")
    
    # Sous-requête avec les grilles et leur nb_passages (exactement comme /analyse - 5 secondes)
    print(f"[zones-sensibles] Étape 2: Calcul des grilles avec passages (comme /analyse)...")
    step_time = time.time()
    grilles_avec_passages_subq = (
        db.session.query(
            Grille.id,
            Grille.geom,
            func.count(TraceFiltered.id).label("nb_passages")
        )
        .outerjoin(
            TraceFiltered,
            and_(
                Grille.geom.op('&&')(TraceFiltered.geom),  # Bounding box check (rapide)
                func.ST_Intersects(Grille.geom, TraceFiltered.geom)  # Intersection précise
            )
        )
        .filter(Grille.geom.isnot(None))
        .group_by(Grille.id, Grille.geom)
        .subquery()
    )
    print(f"[zones-sensibles] Étape 2 terminée: {time.time() - step_time:.2f}s")
    
    # Sous-requête pour calculer le buffer (transformation une seule fois pour précision)
    print(f"[zones-sensibles] Étape 3: Calcul des buffers autour des observations...")
    step_time = time.time()
    # Buffer de 50m avec transformation en métrique puis retour en 4326 (une seule fois)
    obs_with_buffer_subq = (
        db.session.query(
            Obs.id,
            func.ST_Transform(
                func.ST_Buffer(
                    func.ST_Transform(Obs.geom, 3857),  # Transform en Web Mercator
                    50  # Buffer de 50 mètres
                ),
                4326  # Retransform en WGS84
            ).label("buffer_geom")
        )
        .filter(
            Obs.date_debut >= date_min,
            Obs.date_debut <= date_max,
            Obs.cd_nom == cd_nom,
            Obs.geom.isnot(None)
        )
        .subquery()
    )
    print(f"[zones-sensibles] Étape 3 terminée: {time.time() - step_time:.2f}s")
    
    # Requête principale : JOIN optimisé avec && (bounding box) avant ST_Intersects
    print(f"[zones-sensibles] Étape 4: Jointure et calcul des intersections...")
    step_time = time.time()
    query = (
        db.session.query(
            obs_with_buffer_subq.c.id,
            func.ST_AsGeoJSON(obs_with_buffer_subq.c.buffer_geom).label("buffer_geojson"),
            func.max(grilles_avec_passages_subq.c.nb_passages).label("nb_passages_max")
        )
        .select_from(obs_with_buffer_subq)
        .outerjoin(
            grilles_avec_passages_subq,
            and_(
                obs_with_buffer_subq.c.buffer_geom.op('&&')(grilles_avec_passages_subq.c.geom),  # Bounding box check (rapide)
                func.ST_Intersects(
                    obs_with_buffer_subq.c.buffer_geom,
                    grilles_avec_passages_subq.c.geom  # Intersection précise
                )
            )
        )
        .group_by(obs_with_buffer_subq.c.id, obs_with_buffer_subq.c.buffer_geom)
    )
    
    print(f"[zones-sensibles] Étape 4: Exécution de la requête SQL...")
    exec_time = time.time()
    results = query.all()
    print(f"[zones-sensibles] Étape 4 terminée: {time.time() - exec_time:.2f}s (total étape 4: {time.time() - step_time:.2f}s)")
    print(f"[zones-sensibles] Nombre de résultats: {len(results)}")
    
    # Construction du GeoJSON FeatureCollection (calcul zone_sensible en Python)
    print(f"[zones-sensibles] Étape 5: Construction du GeoJSON...")
    step_time = time.time()
    features = [
        {
            "type": "Feature",
            "geometry": json.loads(row.buffer_geojson) if row.buffer_geojson else None,
            "properties": {
                "id": row.id,
                "zone_sensible": (row.nb_passages_max or 0) > 50,
                "nb_passages_max": row.nb_passages_max or 0,
            },
        }
        for row in results
    ]
    print(f"[zones-sensibles] Étape 5 terminée: {time.time() - step_time:.2f}s")
    
    total_time = time.time() - start_time
    print(f"[zones-sensibles] TOTAL: {total_time:.2f}s - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    return jsonify({"type": "FeatureCollection", "features": features})