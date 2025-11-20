from backend.utils.env import db
from geoalchemy2 import Geometry


class EcoCompteurSite(db.Model):
    __tablename__ = "ecocompteur_site"
    __table_args__ = {"schema": "ardeche"}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Unicode)
    geom = db.Column(Geometry("POINT"))


class EcoCompteurVisit(db.Model):
    __tablename__ = "ecocompteur_visit"
    __table_args__ = {"schema": "ardeche"}

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer, db.ForeignKey("ardeche.ecocompteur_site.id"), nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    valeur = db.Column(db.Integer, nullable=False)

    site = db.relationship("EcoCompteurSite", backref=db.backref("visits", lazy=True))
