import os
import redis
from rq import Queue

from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from db import db

from blocklist import BLOCKLIST

from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint
from resources.test import blp as TestBlueprint

# TODO Celery better than RQ


def create_app(db_url=None):
    app = Flask(__name__)
    APP_ROOT = os.path.join(os.path.dirname(__file__))
    FLASK_ENV = os.getenv("FLASK_ENV") or "development"

    ENVIRONMENTS = {
        "development": "dev.env",
        "qa": "qa.env.",
        "production": "production.env",
    }
    dotenv_path = os.path.join(APP_ROOT, ENVIRONMENTS.get(FLASK_ENV) or ".env")
    load_dotenv(dotenv_path)

    redis_connection = redis.from_url(os.getenv("REDIS_URL"))
    app.queue = Queue("emails", connection=redis_connection)
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Store REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv(
        "DATABASE_URL", "sqlite:///data.db"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    migrate = Migrate(app, db)
    api = Api(app)

    # Setup the Flask-JWT-Extended extension
    # Used for signing and verifying JWTs
    app.config["JWT_SECRET_KEY"] = "296499529446623730553873350229123902656"
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        if identity == 1:
            return {"is_admin": True}
        return {"is_admin": False}

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error": "token_expired"}),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "message": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "message": "The token is not fresh.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)
    api.register_blueprint(TestBlueprint)

    return app
