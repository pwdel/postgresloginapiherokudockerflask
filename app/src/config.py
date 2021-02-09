import os

basedir = os.path.abspath(os.path.dirname(__file__))

# environment specific configuration variables
class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False