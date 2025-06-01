from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Configuration for SQLAlchemy
    # Use environment variables for sensitive information like database URIs
    # Default to SQLite for local development if DB_URI is not set
    # For GCP Cloud SQL, the URI will be like:
    # postgresql+psycopg2://<DB_USER>:<DB_PASSWORD>@/<DB_NAME>?host=/cloudsql/<INSTANCE_CONNECTION_NAME>
    # e.g., postgresql+psycopg2://wtl_user:password@/wtl_database?host=/cloudsql/where-to-live-nz:australia-southeast1:wtl-nz-db-pg

    # Simpler local setup for now:
    default_db_uri = 'sqlite:///./local_dev.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', default_db_uri)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Import models here to ensure they are registered with SQLAlchemy
    from . import models

    # Create database tables if they don't exist
    # This is suitable for development. For production, use migrations (e.g., Flask-Migrate).
    with app.app_context():
        db.create_all()

    return app
