# Contenido para: app/config.py

import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

class Config:
    """Configuración base de la app."""
    # Desactiva una función de SQLAlchemy que no usaremos y consume recursos
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Lee la URL de la base de datos desde el archivo .env
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')