from flask import Flask

from backend.routes.routes import routes
from backend.utils.env import db

DATABASE_URL = "postgresql://utilisateur:motdepasse@localhost:5432/nom_de_la_base"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(routes)

    @app.route("/")
    def hello_world():
        return "<p>Hello, World!</p>"

    return app


app = create_app()


if __name__ == "__main__":
    # Crée les tables si elles n'existent pas encore
    with app.app_context():
        db.create_all()
        print("Base de données initialisée avec succès !")
