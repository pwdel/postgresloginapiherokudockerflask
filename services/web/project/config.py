import os
from os import environ, path
# from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

# requires the NPM library called LESS (known to the system as lessc) 
# to be installed on our system in order to compile LESS into CSS.
# equivalent to SASS_BIN
LESS_BIN = '/usr/local/bin/lessc'

# False means Flask-Assets will bundle our static files while we're running Flask in debug mode. 
ASSETS_DEBUG = False

# tell Flask to build our bundles of assets when Flask starts up
ASSETS_AUTO_BUILD = True


# environment specific configuration variables
class Config(object):

    FLASK_ENV = environ.get('FLASK_ENV')
    SECRET_KEY = environ.get('SECRET_KEY')

    # Flask-Assets
    #LESS_BIN = environ.get('LESS_BIN')
    #ASSETS_DEBUG = environ.get('ASSETS_DEBUG')
    #LESS_RUN_IN_DEBUG = environ.get('LESS_RUN_IN_DEBUG')

    # Static Assets
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    # COMPRESSOR_DEBUG = environ.get('COMPRESSOR_DEBUG')

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False