from flask import Blueprint, jsonify

from backend.models.quiet_zone import QuietZone

routes = Blueprint("ardeche", __name__, url_prefix="/api")


@routes.route("/ping", methods=["GET"])
def ping():
    return jsonify(status="ok", message="Ardeche API is alive")


@routes.route("/quiet-zones/species", methods=["GET"])
def list_quiet_zone_species():
    species_rows = (
        QuietZone.query.with_entities(QuietZone.cd_nom)
        .distinct()
        .order_by(QuietZone.cd_nom)
        .all()
    )
    species = [row.cd_nom for row in species_rows if row.cd_nom is not None]
    return jsonify(species=species)
