from flask import Flask, render_template
from app.config import Config
from app.database.connection import init_db
from app.database.seed_data import seed_initial_data
from app.api import api_bp

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)

    # Initialize and seed database
    init_db()
    seed_initial_data()

    # Register blueprints
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
