# modules/report_analyzer/__init__.py
from flask import Flask
from .routes import report_analyzer_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(report_analyzer_bp)
    return app