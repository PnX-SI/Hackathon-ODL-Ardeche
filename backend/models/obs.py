from backend.utils.env import db
from geoalchemy2 import Geometry
from sqlalchemy import DateTime


class Obs(db.Model):
    """
    Observations de biodiv
    """

    __tablename__ = "obs"
    id = db.Column(db.Integer, primary_key=True)
    geom = db.Column(Geometry("POINT", srid=4326))
    cd_nom = db.Column(db.Integer)
    group2_inpn = db.Column(db.String)
    niveau_sensibilite = db.Column(db.String)
    nom_valide = db.Column(db.String)
    date_debut = db.Column(DateTime)
    date_fin = db.Column(DateTime)
    behaviour = db.Column(db.String)
    species_age = db.Column(db.String)
    year_date = db.Column(db.Integer)
    year_month = db.Column(db.Integer)
