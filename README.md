# Flask App on Docker for Heroku with Postgres and Login Capability

## Objective

To deploy a Flask App on Heroku using a Docker image, which uses Postgres and creates a user model with a login capability.

## Past Work

* Previously, I had built a Flask app and deployed to Heroku using just regular virtualenv and Anaconda, as discussed [here](https://github.com/LinkNLearn/homedataflask).
* I also worked with deploying [Docker on Lubuntu 20](https://github.com/pwdel/dockerlubuntu).
* Most recently I worked on creating a [Flask app and deployed it on Heroku using Docker](https://github.com/pwdel/herokudockerflask).

## Software Planning

### Local Development

1. Use the basic [Flask app deployed on Heroku using Docker](https://github.com/pwdel/herokudockerflask) discussed above.
2. In the Dockerfile, add volumes for Postgres and instructions to include a database as well as installation procedures.
3. Start a new Heroku app, login and provision the app, ensuring that it works along with Postgres.
4. Setup Web Forms on Flask, Allow Web Forms to Talk to Database
5. Setup Password Hashing
6. Use flask-login library, implement it.
7. Setup User model
8. Allow login and logout functionality
9. Setup user registration

### Setting Up the Basic, Previously Used Flask App

We're going to keep everythin the same with this app - the only change that we need to make is the outgoing message. Rather than, "Hello World, Little Dude!" we will slightly modify this for recogtion purposes.

We'll make it say, "Hello World, Little Dude, How Are You?"  Other than that we'll just copy and paste the previous code.

### Setting Up Dockerfile for Postgres and Other Functionality

First off, we're going to set some environmental variables.

* ENV PYTHONDONTWRITEBYTECODE, which prevents bytecodes from being written to disk, or .pyc files, which is basically Python source code.
* ENV PYTHONUNBUFFERED, which prevents Python from buffering stdout and stder, which are basically data streams on linux (as opposed to merely displaying on a terminal window).

```
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
```
Of course to test things after we have added the above and modified the app, we can first build the image, but our dedicated port at 5000 is already in use, so we need to shut down any other apps currently running on that port within docker using:

```
sudo docker stop cacee7836f5b
```

...which stops the process, after which we can bring up our newly created docker image on the proper port.

### Adding Postgres Functionality

Within our docker file, docker-compose.yml we need to add several key components:

```
    depends_on:
      - db
  db:
    image: postgres:13-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=hello_flask
      - POSTGRES_PASSWORD=hello_flask
      - POSTGRES_DB=hello_flask_dev

volumes:
  postgres_data:
```

[Postgres versioning is discussed here](https://www.postgresql.org/support/versioning/), with, "alpine," indicating that the Postgres version is based off of Alpine Linux, which is a super small version of Linux that can be run from RAM only.

The above is for development mode, so we just use a stock username and password, however when we use these variables on Heroku we can store them as environmental variables.

The 'volumes' section is used to persist the data beyond the lifetime of a container.

We also need to add:

```
DATABASE_URL=postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev
```

...to the .env.dev file to indicate the database URL for dev.

We update the server.py app a bit, adding jsonify to create a json-style, API type output.  We also renamed this file, "__init__.py" as this seems to be the convention.


We created config.py in the /src folder to setup environment-specific variables.

```
import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

```

We then added the following to server.py to call these variables:

```
app.config.from_object("project.config.Config")
```

Finally, we add [Flask Alchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) for SQL inputs and outputs as well as [Psycopg](https://www.psycopg.org/) for Postgres management.

```
Flask-SQLAlchemy==2.4.1
psycopg2-binary==2.8.4

```

We then add:

```
db = SQLAlchemy(app)
```

To server.py in order to be able to call the SQALchemy library.

However, when we run "sudo docker-compose build "

We get the error:

```
pg_config is required to build psycopg2 from source.  Please add the directory                                                          
    containing pg_config to the $PATH or specify the full executable path with the                         
```

Basically, using alpine linux, everything has to be built from source, since it is such a slimmed down version of linux.  So, we can attempt to use the non-alpine version of Postgres and build again.  However, upon attempting to take out the, "-alpine" in:

```
  db:
    image: postgres:13-alpine
```

We see the same error.  On the [docs recommended by the command line](https://www.psycopg.org/docs/install.html), we see that psycopg recommends installation from binary with "pip install psycopg2-binary."  We can attempt to add this directly on our Dockerfile.

However, the requirements.txt already include "psycopg2-binary==2.8.4" - looking more closely at the shell error we see that it says, "No matching distribution found for psycopg2-binary==2.8.4" - so likely this just means we are not using a valid version of psycopg2-binary.

We can find the latest version of the [psycopg2-binary here](https://pypi.org/project/psycopg2-binary/), which at the time of writing this appears to be 2.8.6.

We can re-do the image build and spin up the container:

```
sudo docker-compose build

sudo docker-compose up -d
```

We see that we then have the following under "sudo docker ps"

| CONTAINER ID | IMAGE              | COMMAND                | PORTS    | NAMES                                  |
|--------------|--------------------|------------------------|----------|----------------------------------------|
| 23c5cc7008d7 | postgres:13-alpine | "docker-entrypoint.s…" | 5432/tcp | postgresloginapiherokudockerflask_db_1 |

However, we don't see the actual app being served on port 5000. However, we do see the webapp image, upon inspection as shown below.

| REPOSITORY                            | TAG             | IMAGE ID     | SIZE  |
|---------------------------------------|-----------------|--------------|-------|
| postgresloginapiherokudockerflask_web | latest          | cf6adcfb5a11 | 141MB |
| python                                | 3.9-slim-buster | d5d352d7d840 | 114MB |
| postgres                              | 13-alpine       | 8c6053d81a45 | 159MB |


### Applying a Model to the Database

manage.py


## References

[Dockerizing Flask with Postgres, Gunicorn and Nginx](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/)
[Flask Mega Tutorial: Logins](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins)
[Flask-Login](https://flask-login.readthedocs.io/en/latest/)