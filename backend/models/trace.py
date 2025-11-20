from backend.utils.env import db
from geoalchemy2 import Geometry


class Trace(db.Model):
    """
    Traces gpx
    """

    __tablename__ = "trace"
    id = db.Column(db.Integer, primary_key=True)
    track_id = db.Column(db.Integer)
    date_start = db.Column(db.Date)
    date_end = db.Column(db.Date)
    geom = db.Column(Geometry("MULTIPOLYGON"))


class Grille(db.Model):
    """
    Grille
    """

    __tablename__ = "grille_200_4326"
    id = db.Column(db.Integer, primary_key=True)
    geom = db.Column(Geometry("MULTIPOLYGON"))