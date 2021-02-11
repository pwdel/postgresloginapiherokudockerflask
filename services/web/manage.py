import click
from flask.cli import FlaskGroup

from project import app, db
from project import User

cli = FlaskGroup(app)

@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()

@cli.command("seed_db")
def seed_db():
    db.session.add(User(email="test@test123.net"))
    db.session.commit()


@cli.command("test_message")
def seed_db():
	click.echo('hey this is a test message, thanks for reading!')

if __name__ == "__main__":
    cli()