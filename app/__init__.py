# Contenido para: app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

# Inicializamos la Base de Datos (db) y Migrate
# Los declaramos aquí globalmente pero vacíos
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    """Factory para crear la instancia de la aplicación Flask."""
    
    app = Flask(__name__)
    
    # Cargar la configuración desde la clase Config
    app.config.from_object(config_class)

    # Conectar nuestras instancias (db, migrate) con la app
    db.init_app(app)
    migrate.init_app(app, db)

    # --- Registrar Blueprints (nuestras rutas/endpoints) ---
    # Importamos nuestro blueprint de rutas
    from .routes import api_bp
    # Registramos el blueprint. Todas estas rutas empezarán con /api
    app.register_blueprint(api_bp, url_prefix='/api')

    return app