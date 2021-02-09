from flask import Flask, jsonify
import os

server = Flask(__name__)

port = int(os.environ.get("PORT", 5000))

@server.route("/")

app.config.from_object("project.config.Config")

db = SQLAlchemy(app)

def hello():
    return jsonify(answer="Hello World, Little Dude, How Are You?")

if __name__ == "__main__":
   server.run(host='0.0.0.0',port=port)