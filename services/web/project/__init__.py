from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
# import flask LoginManager
from flask_login import LoginManager

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
    # initialize database plugin
    db.init_app(app)
    # initialize login manager plugin
    login_manager.init_app(app)
    with app.app_context():
        from . import routes
        from . import auth
        from .assets import compile_assets

        # Register Blueprints
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)

        # Create Database Models
        db.create_all()

        # Compile static assets
        if app.config['FLASK_ENV'] == 'development':
            compile_assets(app)

    return app

app = create_app()

# insert database model class
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

# create default route for user login
# define def login(self,xxx) as a function which defines the login code
@app.route('/login', methods=['POST'])
def login():
    info = json.loads(request.data)
    username = info.get('username', 'guest')
    password = info.get('password', '') 
    user = User.objects(name=username,
                        password=password).first()
    if user:
        # the actual code for the user login
        login_user(user)
        return jsonify(user.to_json())
    else:
        return jsonify({"status": 401,
                        "reason": "Username or Password Error"})

def hello():
    return jsonify(answer="Hello World, Little Dude, How Are You?")

if __name__ == "__main__":
   app.run(host='0.0.0.0',port=port)
