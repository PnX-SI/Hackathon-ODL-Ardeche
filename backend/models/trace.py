from utils.env import db
from geoalchemy2 import Geometry


class Trace(db.Model):
    """
    Traces gpx
    """

    __tablename__ = "trace"
    __table_args__ = {"schema": "ardeche"}
    id = db.Column(db.Integer, primary_key=True)
    tack_id = db.Column(db.Integer)
    date_start = db.Column(db.Date)
    date_end = db.Column(db.Date)
    geom = db.Column(Geometry("MULTIPOLYGON"))
