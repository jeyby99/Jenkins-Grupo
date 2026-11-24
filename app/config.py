"""Configuración de la aplicación.

ERROR INTENCIONAL 1 (lo detecta SonarQube):
la contraseña está escrita directamente en el código. Cualquiera que vea
el repositorio la conoce.
Corrección: leerla de una variable de entorno, por ejemplo
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
"""

import os

DB_USER = "calculadora"
DB_PASSWORD = "Qu1t0-Pasaje-2026!"


class Config:
    # Flask la usa para firmar la cookie de sesión (Flask-Login la necesita).
    SECRET_KEY = os.environ.get("SECRET_KEY", "solo-para-desarrollo")

    # SQLite: un solo archivo. Flask-SQLAlchemy lo crea en la carpeta instance/.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///calculadora.db")
