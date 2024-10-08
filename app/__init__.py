from flask import Flask
from .routes import main

def create_app():
    app = Flask(__name__)

    # Registrar las rutas desde el archivo routes.py
    app.register_blueprint(main)

    return app