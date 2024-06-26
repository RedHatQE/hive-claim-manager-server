import os
from typing import Any, Dict, List, Tuple
from flask import Flask, Response, request, send_file
from flask import jsonify, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
from config import ApplicationConfig
from models import db, User
from pyaml_env import parse_config

from utils import (
    claim_cluster,
    claim_cluster_delete,
    delete_all_claims,
    get_all_claims,
    get_all_user_claims_names,
    get_cluster_pools,
)

DB_URI = os.path.join("/tmp", "db.sqlite")
app = Flask("hive-claims-manager")
app.config.from_object(ApplicationConfig)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)
server_session = Session(app)
db.init_app(app)


def create_users() -> None:
    _config = parse_config(os.environ["HIVE_CLAIM_FLASK_APP_USERS_FILE"])
    password = _config["password"]
    for user in _config["users"]:
        hashed_password = bcrypt.generate_password_hash(password)
        new_user = User(name=user, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()


with app.app_context():
    db.drop_all()
    db.session.commit()
    db.create_all()
    create_users()
    db.session.commit()


@app.route("/healthcheck")
def healthcheck() -> str:
    return "alive"


@app.route("/@me")
def get_current_user() -> Tuple[Response, int]:
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user: Any = User.query.filter_by(id=user_id).first()
    return jsonify({"id": user.id, "name": user.name}), 200


@app.route("/login", methods=["POST"])
def login_user() -> Tuple[Response, int]:
    name = request.json["name"]
    password = request.json["password"]

    user: Any = User.query.filter_by(name=name).first()

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401

    session["user_id"] = user.id

    return jsonify({"id": user.id, "name": user.name}), 200


@app.route("/logout", methods=["POST"])
def logout_user() -> str:
    session.pop("user_id")
    return "200"


@app.route("/cluster-pools", methods=["GET"])  # type: ignore[type-var]
def cluster_pools_endpoint() -> List[Dict[str, str]]:
    return get_cluster_pools()


@app.route("/cluster-claims", methods=["GET"])  # type: ignore[type-var]
def cluster_claims_endpoint() -> List[Dict[str, str]]:
    return get_all_claims()


@app.route("/claim-cluster", methods=["POST"])
def claim_cluster_endpoint() -> Tuple[Dict[str, str], int]:
    _user: str = request.args.get("user", "")
    _pool_name: str = request.args.get("name", "")
    if not _user or not _pool_name:
        return {"error": "User or Pool name missing", "name": ""}, 401

    return claim_cluster(user=_user, pool=_pool_name), 200


@app.route("/delete-claim", methods=["POST"])
def delete_claim_endpoint() -> Tuple[Response, int]:
    _claim_name: str = request.args.get("name", "")
    _user: str = request.args.get("user", "")
    if _user not in _claim_name:
        return jsonify({"error": "User is not allowed to delete this claim", "name": ""}), 401

    claim_cluster_delete(claim_name=_claim_name.strip())
    return jsonify({"deleted": _claim_name}), 200


@app.route("/all-user-claims-names", methods=["GET"])
def all_user_claims_names_endpoint() -> Tuple[Response, int]:
    _user: str = request.args.get("user", "")
    return jsonify(get_all_user_claims_names(user=_user)), 200


@app.route("/delete-all-claims", methods=["POST"])
def delete_all_claims_endpoint() -> Tuple[Response, int]:
    _user: str = request.args.get("user", "")
    return jsonify(delete_all_claims(user=_user)), 200


@app.route("/kubeconfig/<filename>", methods=["GET"])
def download_kubeconfig_endpoint(filename: str) -> Response:
    return send_file(f"/tmp/{filename}", download_name=filename, as_attachment=True)  # type: ignore[call-arg]


def main() -> None:
    app.logger.info(f"Starting {app.name} app")
    app.run(
        port=int(os.getenv("HIVE_CLAIM_FLASK_APP_PORT", 5000)),
        host=os.getenv("HIVE_CLAIM_FLASK_APP_HOST", "0.0.0.0"),
        use_reloader=bool(os.getenv("HIVE_CLAIM_FLASK_APP_RELOAD", False)),
        debug=bool(os.getenv("HIVE_CLAIM_FLASK_APP_DEBUG", False)),
    )


if __name__ == "__main__":
    main()
