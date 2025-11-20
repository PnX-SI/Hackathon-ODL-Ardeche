import json

from flask import Blueprint, jsonify, request

from backend.models.obs import Obs
from backend.models.quiet_zone import QuietZone
from backend.utils.env import db
from sqlalchemy import func

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

    snapped_geom = func.ST_SnapToGrid(Obs.geometry, cell_size)
    query = db.session.query(
        func.ST_AsGeoJSON(snapped_geom).label("geom_geojson"),
        func.count().label("count"),
    ).filter(Obs.geometry.isnot(None))

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
