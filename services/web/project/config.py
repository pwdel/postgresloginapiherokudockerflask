import os

basedir = os.path.abspath(os.path.dirname(__file__))

# requires the NPM library called LESS (known to the system as lessc) 
# to be installed on our system in order to compile LESS into CSS.
LESS_BIN = '/usr/local/bin/lessc'

ASSETS_DEBUG = False
ASSETS_AUTO_BUILD = True


# environment specific configuration variables
class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False