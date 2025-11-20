from backend.utils.env import db
from geoalchemy2 import Geometry


class Obs(db.Model):
    """
    Observations de biodiv
    """

    __tablename__ = "obs"
    id = db.Column(db.Integer, primary_key=True)
    cd_nom = db.Column(db.Integer)
    nom_valide = db.Column(db.Unicode)
    geometry = db.Column(Geometry("POINT"))
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    behaviour = db.Column(db.Unicode)
    species_age = db.Column(db.Unicode)
    niveau_sensibilite = db.Column(db.Unicode)
