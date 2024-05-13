import os
import redis


DB_URI = os.path.join("/tmp", "db.sqlite")


class ApplicationConfig:
    SECRET_KEY = os.environ["HIVE_CLAIM_FLASK_APP_SECRET_KEY"]

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_URI}"

    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_REDIS = redis.from_url("redis://127.0.0.1:6379")
