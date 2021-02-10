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
4. Ensure database working
5. Setup Web Forms on Flask, Allow Web Forms to Talk to Database
6. Setup Password Hashing
7. Use flask-login library, implement it.
8. Setup User model
9. Allow login and logout functionality
10. Setup user registration

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


Note that the above port mentioned is Port 5432/tcp. Note this is the PostgreSQL Database port, and it uses tcp protocol.

One file that we have had which we haven't activated yet is the entrypoint.sh file.  If we take a look at this file:

```
#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python server.py create_db

exec "$@"
```
Basically, it is sort of a bootstrapping file which gets everything set up in order, including running the server.py file, which in turn instructs the app to serve on PORT 5000. However, we should also keep in mind that there is a paradigm within Docker that different services should be running in different containers, namely that the app should run in a different container than the Postgres database. It's not clear at the moment how the app is going to run or what part of our entire software setup here will allow that to happen.

As of now, we have the entrypoint.sh file commented out within the Dockerfile.  We can change this in favor of our CMD to run the app.

```
# make entrypoint.sh executable
RUN chmod +x entrypoint.sh

# use entrypoint.sh as entrypoint
ENTRYPOINT ["entrypoint.sh"]

# command to run on container start
# CMD [ "python", "./server.py" ] 
```

After doing this, we get an error: "no such file or directory" which means the file system is not pointing toward the entrypoint.sh properly. 

However, what we also notice is that there is an alternate way to run the flask file seperately from the Postgres database.  Basically, we have to build two seperate images and then run a second container seperately by feeding in the right environmental variables.

There are three environmental variables we have:

```
FLASK_APP
FLASK_ENV
DATABASE_URL
```
And the images we have built are shown in the table above, which include "postgresloginapiherokudockerflask_web" as well as "postgres."

The first command that we do is basically to build the Dockerfile.  We use [docker build options](https://docs.docker.com/engine/reference/commandline/build/):

* "-f" to specify the file. We use this to specify a specific Dockerfile.
* "-t" to tag the image once built.  So for example if we want to name the image, "flask_only:latest" we would put, "-t flask_only:latest" where the tag, "latest" will be applied to the name, "flask_only"
* the ./ argument at the end shows where we are building from.

```
$ docker build -f ./Dockerfile -t flask_postgres:latest ./
```
Next, we run on port 5001:5000, seperate from the default Postgres port.  We use [docker run options](https://docs.docker.com/engine/reference/commandline/run/)

* "-p" which allows us to select the port.
* "-e" which allows us to set environmental variables

```
$ sudo docker run -p 5001:5000 \
    -e "FLASK_APP=project/server.py" -e "FLASK_ENV=development" \
    flask_postgres
```

So right away we get an, "invalid syntax" error, based upon the configuration file.

```
  File "/app/./server.py", line 10                                                                            
    app.config.from_object("project.config.Config")                                                           
    ^                                                                                                         
SyntaxError: invalid syntax 
```

Part of what I should reflect on at this point is that I have not been using the standard naming conventions typically seen on Flask tutorials online. Rather than, "server.py" folks typically use __init__.py as the initialization file, and they may call the Flask application, "app" rather than server internally within that init file. At the same time, it's probably valuable, for learning purposes, to use a different naming structure, in order to force my way through this and understand how everything fundamentally connects together, rather than merely copying and pasting.

So that being said, we have a invalid syntax error based upon a flask command. We can check out the [documentation here](https://flask.palletsprojects.com/en/1.1.x/config/). The documentation says under, "Configuring from Files,":

> Configuration becomes more useful if you can store it in a separate file, ideally located outside the actual application package. This makes packaging and distributing your application possible via various package handling tools (Deploying with Setuptools) and finally modifying the configuration file afterwards.

> So a common pattern is this:

> app = Flask(__name__)
> app.config.from_object('yourapplication.default_settings')

For a complete explination of this exact line, we are referred to the [class flask.Config() documentation](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Config). Further this documentation refers to [from_object(obj)](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Config.from_object).

> Objects are usually either modules or classes. from_object() loads only the uppercase attributes of the module/class. A dict object will not work with from_object() because the keys of a dict are not attributes of the dict class.

Within our config.py file, we have the following class:

```
class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

Also that we should note that we have our config.py file within the /src folder, along with our server.py folder.  Note that the Python documentation mentions:

> Make sure to load the configuration very early on, so that extensions have the ability to access the configuration when starting up.

Previously, we had our @server.route("/") happening above our server.config.from_object() command, so it is not clear whether this may have not allowed something important, such as the database, to access this configuration when starting up.

So, to try to make this easier, we put a config.cfg file rather than a config.py file with a class in the /src folder, and used only the variablenames as a test to see if we could successfully build.

```
    SQLALCHEMY_DATABASE_URI = "DATABASE"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

We also notice that the Config(object) class refers to SQAlchemy.  When we look at our main server.py code, we note that we have:

```
db = SQLAlchemy(app)
```
Which probably should be: "db = SQLAlchemy(server)" since we don't have anything named, "app."

So with the above changes, we can attempt to build the image and run.  After doing so, we get the error:

```
NameError: name 'SQLAlchemy' is not defined
```
This is of course because we did not include, "from flask_sqlalchemy import SQLAlchemy" within our server.py docker file. So, we just rebuild and re-run.

Upon fixing this, we then get a successful result, with the capability to view the flask app with a json output at port 5001. Confusingly, the terminal output reads the following:

```
* Serving Flask app "server" (lazy loading)                                                                                                              
 * Environment: development                                                                                                                               
 * Debug mode: on                                                                                                                                         
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)                                                                                                 
 * Restarting with stat                                                                                                                                   
 * Debugger is active!                                                                                                                                    
 * Debugger PIN: 137-442-796                                                                                                                              
172.17.0.1 - - [10/Feb/2021 13:31:56] "GET / HTTP/1.1" 200 -  

```

* Why does the terminal say that we're hosting on port 5000 when really it's on 5001?
* We're going to need the config.py file to be called in order to work with Docker-Compose specifically the object inside of that, how can we debug it?

First, let's investigate how to pull from the config.py file, since this is going to be needed to fully deploy.


What seems to be important in calling config.py is understanding:

1) The application structure, basically how we have our folders laid out and what goes in which folder.
2) Where the server.config.from_object("config.Config") function actually calls a particular object, based upon "config.Config" and the location of config.py.
3) The basedir = os.path.abspath(os.path.dirname(__file__)) function.

So first off, our application structure is as follows:

└── .env.dev
└── Dockerfile
└── docker-compose.yml
└── entrypoint.sh
└── app
    └── requirements.txt
    └── src
        └── server.py
        └── config.py 

Secondly, we don't know exactly where server.config.from_object("config.Config") is pulling the file. This call is what is known as an, "import" which in Python3 is known as an [absolute import](https://www.python.org/dev/peps/pep-0008/#imports) which is touched on in that documentation file. Basically this seems to indicate that our from_object("object") should point exactly to where the item is located, at src.config.Config. However, this migtht also mean that we should move the config.py file to the /app folder and simply access it with config.Config.

First, we can try the src.config.Config method to see if this works.

After attempting these two methods, we found that using the following code worked to call the config.py file properly, while keeping the config.py file in the src folder.:

```
# pull the config file, per flask documentation
server.config.from_object("config.Config")
```

Thirdly, basedir = os.path.abspath(os.path.dirname(__file__)) seemed to work given the above, so there is likely no need to change it.

Finally, we can try to build the entire app using docker-compose, including the database, so that they can run together.  Once we have done this, we get the following (note - we had to modify docker-compose.yml to include container_name and image in order to shorten up and customize the names to how we wanted them:

| CONTAINER ID | IMAGE              | COMMAND                | STATUS        | PORTS                  | NAMES |
|--------------|--------------------|------------------------|---------------|------------------------|-------|
| 00713c704200 | hello_flask        | "python server.py ru…" | Up 6 seconds  | 0.0.0.0:5000->5000/tcp | flask |
| 03855169ac90 | postgres:13-alpine | "docker-entrypoint.s…" | Up 11 seconds | 5432/tcp               | db    |


So now we are showing that both Postgres and Flask are running.  We are able to visit localhost:5000 to see the flask app, but we don't know for sure if Postgres is really working, and we don't have anything in the database yet.

Before we move into production, we have a couple tasks that we should accomplish:

1. Create the database table.
2. Ensure the table was created.
3. Check that the volume was created in Docker with "volume inspect"
4. Add an entrypoint.sh to verify that Postgres is up and healthy *before* creating the database table and running the Flask development server.
5. Install [Netcat](http://netcat.sourceforge.net/) networking utility to read and write across network connections using the TCP/IP protocol.
6. Add SQL_HOST, SQL_PORT, DATABASE environmental variables for the entrypoint.sh script to ensure extant for database.
7. Add some sample users to the table via a CLI command we build.

After these are accomplished, we can start to move forward into production, which involves creating production env variables and a production Dockerfile.  We have already moved things into production once, and have implemented Gunicorn, so this should not be so much work.

This may involve creating a new project structure.

## Ensure Database Working

### Creating Database Table

### Ensure Table Was Created

### Check Volume Was Created

### Add entrypoint.sh to Verify Postgres Health

### Install Netcat

### Add Environmental Variables

### Add Sample Users, Sample Data

## Pushing to Production

### Production .evn Files

### Production Dockerfiles

## Webforms on Flask

## Password Hashing

## Flask Login Library

## User Model

## Login and Logout Functionality

## User Registration

## Pushing Everything to Production

## Conclusion



--------------


If we want to add a management python cli within manage.py.

```
$ sudo docker run -p 5001:5000 \
    -e "FLASK_APP=project/server.py" -e "FLASK_ENV=development" \
    flask_only python /usr/src/app/manage.py run -h 0.0.0.0
```


So basically we specify the exact file that we want to build, and then the port it should run on to check things for sanity purposes.

### Applying a Model to the Database

manage.py


## References

[Dockerizing Flask with Postgres, Gunicorn and Nginx](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/)
[Flask Mega Tutorial: Logins](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins)
[Flask-Login](https://flask-login.readthedocs.io/en/latest/)