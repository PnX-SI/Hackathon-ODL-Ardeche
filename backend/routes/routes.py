from flask import Blueprint, request, g

routes = Blueprint("ardeche", __name__)


@routes.route("/", methods=["GET"])
def test():
    return "HAAAAAAAAAAAa"
