from utils.env import db
from geoalchemy2 import Geometry


class QuietZone(db.Model):
    """
    Zone de quietude
    """

    __tablename__ = "quiet_zone"
    __table_args__ = {"schema": "ardeche"}
    id = db.Column(db.Integer, primary_key=True)
    cd_nom = db.Column(db.Integer)
    nom_valide = db.Column(db.Unicode)
    geom = db.Column(Geometry("MULTIPOLYGON"))
