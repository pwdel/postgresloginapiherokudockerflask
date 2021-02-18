
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
# import flask LoginManager
from flask_login import LoginManager
# import flask_assets
from flask_assets import Environment, Bundle
# import compile assets from assets.py
from .assets import compile_static_assets

port = int(os.environ.get("PORT", 5000))

# activate SQLAlchemy
db = SQLAlchemy()
# set login manager name
login_manager = LoginManager()

def create_app():
    # construct core app object, __name__ is the default value.
    app = Flask(__name__)
    # pull the config file, per flask documentation
    # Application configuration
    app.config.from_object("project.config.Config")

    # Set environment for assets
    assets = Environment()

    # initialize database plugin
    db.init_app(app)

    # initialize asset plugin
    assets.init_app(app)

    # initialize login manager plugin
    login_manager.init_app(app)
    with app.app_context():
        from . import routes
        from . import auth
        from .assets import compile_static_assets
        # Register Blueprints
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)

        # import model class
        from . import models

        # Create Database Models
        db.create_all()

        # Compile static assets
        compile_static_assets(assets)
        
    return app

# Physically create the app now
app = create_app()


if __name__ == "__main__":
   app.run(host='0.0.0.0',port=port)
