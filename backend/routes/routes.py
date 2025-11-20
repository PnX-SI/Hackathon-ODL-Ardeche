from flask import Blueprint, jsonify

from backend.models.obs import Obs
from backend.models.quiet_zone import QuietZone

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
