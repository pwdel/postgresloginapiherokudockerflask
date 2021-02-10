from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

server = Flask(__name__)

port = int(os.environ.get("PORT", 5000))

# pull the config file, per flask documentation
server.config.from_object("config.Config")

# pull the config file as a python file
# server.config.from_pyfile("config.cfg")

# activate SQLAlchemy
db = SQLAlchemy(server)


# run server
@server.route("/")


# insert database model

def hello():
    return jsonify(answer="Hello World, Little Dude, How Are You?")

if __name__ == "__main__":
   server.run(host='0.0.0.0',port=port)