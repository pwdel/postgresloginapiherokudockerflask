from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)

port = int(os.environ.get("PORT", 5000))

# pull the config file, per flask documentation
app.config.from_object("project.config.Config")

# activate SQLAlchemy
db = SQLAlchemy(app)

# insert database model
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    def __init__(self, email):
        self.email = email

# run app
@app.route("/")
def home():
	return render_template('home.html')

# route to about page
@app.route('/about/')
def about():
    return render_template('about.html')



def hello():
    return jsonify(answer="Hello World, Little Dude, How Are You?")

if __name__ == "__main__":
   app.run(host='0.0.0.0',port=port)
