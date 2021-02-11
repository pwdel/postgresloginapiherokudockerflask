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

So to enter a table into the database, we need some way to manage the database, which means a CLI.  For this, that means creating a manage.py and using [docker-compose exec](https://docs.docker.com/compose/reference/exec/) to run an arbitrary command within the service.

manage.py:

```
from flask.cli import FlaskGroup

import server, db

cli = FlaskGroup(server)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


if __name__ == "__main__":
    cli()
```
Basically this creates a command, "create_db" which allows us to run from the command line to apply a model to the database.

Here again, if we had included a, "from src import server" we get a, "ModuleNotFoundError: No module named 'src'."  Basically, since the manage.py file is already in the src folder, there is no way to physically go in and import from it - so we do not include this portion, but rather just simply, "import server" which essentially imports our server.py file directly as a module.

As far as the [FlaskGroup()](https://flask.palletsprojects.com/en/1.1.x/api/#flask.cli.FlaskGroup) function goes, this is a part of the Command Line Interface, CLI. FlaskGroup is basically a type of [AppGroup](https://flask.palletsprojects.com/en/1.1.x/api/#flask.cli.AppGroup) which wraps all functions in a folder within a group, and allows subcommands to be attached ,per [click.Group()](https://click.palletsprojects.com/en/7.x/api/#click.Group) as a dictionary of commands, a sort of library.

Part of our confusion at this point is that we have a file named server.py and then within that file we have a function where we name the flask app, "server = Flask(__name__)" - which basically means, we have two things named "server," with different points of our program calling out, "server," creating a sort of spaghetti code.

So to clean this up, we renamed, "server" as "app" within the server.py file. However, upon running the file again, we see that we can't seem to locate the module, "db." Rather than continue making spaghetti code, it would be good to do some refactoring to keep us going in a good direction.

#### Refactoring

Our designed project structure is:

├── .env.dev

├── .env.prod

├── .env.prod.db

├── .gitignore

├── docker-compose.prod.yml

├── docker-compose.yml

└── services

    ├── nginx

    │   ├── Dockerfile

    │   └── nginx.conf

    └── web

        ├── Dockerfile

        ├── Dockerfile.prod

        ├── entrypoint.prod.sh

        ├── entrypoint.sh

        ├── manage.py

        ├── project

        │   ├── __init__.py

        │   └── config.py

        └── requirements.txt


So we started out by moving everything into the folders as shown in the above.

After this shift, we are going to have to diagnose a lot of errors.

##### Dockerfile

* I started out by running the python files in roder of how they occur. Since we are trying to build a management app, we try to run manage.py first and debug the app itself one piece at a time, changing variable names to fit the project structure.

* We need to address the Dockerfile symlinks message. This can be addressed by adding a, "." to the end of the command.

```$ sudo docker build .```

* The requirements.txt file was actually run twice in the Dockerfile, which is not desireable anyway!  Good catch. Once we eliminated the wrong filename from the requirements.txt file, that eliminated another error.

After the three above changes, there is a need to work with docker-compose, which requires docker-compose.yml.

* This required a change in the .env.dev file to use __init__.py
* This also required a change in docker-compuse.yml to use __init__.py
* We get a message, "unable to prepare context: unable to evaluate symlinks in Dockerfile path"  This is because of how the docker-compose.yml file is pointed toward the, "build" path. Previously it was set to, ./ because the Dockerfile was in the root directory, but now we are building in /services/web/ directory.

```
services:
  web:
    image: hello_flask
    container_name: flask
    build: ./services/web/
```
* With this, the image is properly built using composer.
* Next we have to see if we can run it.

We use the custom build code:

```
sudo docker run -p 5001:5000 \
    -e "FLASK_APP=project/services/web/__init__.py" -e "FLASK_ENV=development" \
    hello_flask
```

When we run the above, we get an error referring to server.py. If we do a search in our project we see two more locations where this still exists:

```
./services/web/Dockerfile:
   22  
   23  # command to run on container start
   24: CMD [ "python", "./server.py" ] 

./services/web/entrypoint.sh:
   12  fi
   13  
   14: python server.py create_db
   15  
   16  exec "$@"
```

We repaced these with the proper __init__.py file, however every time we try to run our Docker image, we get an error looking for server.py. So, we shut down all of our containers and removed all of our images to start off with a clean slate.

Upon running sudo docker-compose build we get a slightly different command prompt that comes out:

```
Step 8/8 : CMD [ "python", "./services/web/project/__init__.py" ]

```

Of course, this does not spin up the actual database, which would need to be built through the entrypoint.sh file. But we're not that far yet, we just need to make sure the flask app is working.

Fortunately this time we get a slightly different error,

```
python: can't open file '/usr/src/app/./services/web/project/__init__.py': [Errno 2] No such file or directory
```

Which basically means that the CMD file can't be executed. Which, based upon the build command we're trying to run which manually runs flask on port 5001, we don't even really need at the moment.

Interestingly, when we run: "sudo docker-compose logs"

We see that the db, postgres is running correctly.  However, we see:

```
flask  | python: can't open file '/usr/src/app/__init__.py': [Errno 2] No such file or directory 
```
Evidently, there is a way to actually go into the docker container and look at the actual running container through bash to find out where the file is aDockerfile in the proper location.  Currently in the dockerfile, we are using /usr/src/app as the location to copy the project, however the reality inside of the container may look different.

After verifying that the Flask app is indeed running, we do:

```
sudo docker run --rm -it hello_flask bash
```
From this point we are actually logged into the container via bash and we have the following prompt:

```
root@25fdd88318d9:/usr/src/app# ls

Dockerfile  entrypoint.sh  manage.py  project  requirements.txt  


root@25fdd88318d9:/usr/src/app# cd project


root@25fdd88318d9:/usr/src/app/project# ls

__init__.py  __pycache__  config.py  
```

So from here, using 'pwd' we can see that the path we need to be using should be:

```
/usr/src/app/project/__init__.py
```

We can even test out the command within the root@container by running a python command. After doing so we get:

```
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```
##### docker-compose.yml

The problem appears to have been in our docker-compose.yml file. Keep in mind, docker-compose uses the .yml file, whereas docker build uses the dockerfile. docker-compose.yml is a set of instructions just like the dockerfile. Previously we had:

```
    command: python __init__.py run -h 0.0.0.0
    volumes:
      - ./app/:/src/
```

However given what we know about the directory structure inside of the Dockerfile, we now need:

```
    build: ./services/web
    command: python manage.py run -h 0.0.0.0
    volumes:
      - ./services/web/:/usr/src/app/
```

Note, since we're using the manage.py file to access everything, we need to make this file executable.  However, re-doing the image, we get:

```
ModuleNotFoundError: No module named 'config'
```

Which is tied to our config.py file and our from_object discussion above. So we now can change our __initi__.py file to:

```
# pull the config file, per flask documentation
app.config.from_object("project.config.Config")
```

This error does not go away after running, so we may need to rebuild the image from scratch. However upon visiting localhost:5000 we now see that something is running, albiet with a typeerror.  Once we build everything again, we see an error free log through docker:

```
db     |                                                                                                                                                                         
db     | PostgreSQL Database directory appears to contain a database; Skipping initialization
db     | 
db     | 2021-02-11 00:55:29.024 UTC [1] LOG:  starting PostgreSQL 13.1 on x86_64-pc-linux-musl, compiled by gcc (Alpine 10.2.1_pre1) 10.2.1 20201203, 64-bit
db     | 2021-02-11 00:55:29.024 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
db     | 2021-02-11 00:55:29.024 UTC [1] LOG:  listening on IPv6 address "::", port 5432
db     | 2021-02-11 00:55:29.342 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db     | 2021-02-11 00:55:29.759 UTC [21] LOG:  database system was shut down at 2021-02-11 00:51:42 UTC
db     | 2021-02-11 00:55:29.897 UTC [1] LOG:  database system is ready to accept connections
flask  |  * Serving Flask app "project/__init__.py" (lazy loading)
flask  |  * Environment: development
flask  |  * Debug mode: on
flask  |  * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
flask  |  * Restarting with stat
flask  |  * Debugger is active!
flask  |  * Debugger PIN: 113-399-322

```
Of course over at localhost:5000 we still see an error, because we need to add to the database but overall we successfully launched the app and database.

### Ensure Table Was Created

Next we can go and make sure the table was created with:

```
$ docker-compose exec web python manage.py create_db
```
We get the error: "NameError: name 'db' is not defined"

This is because we have to import db on the manage.py file:

```
from project import app, db
```

Restart with:

```
docker-compose up -d --build
```

We are able to check the actual table with:

```
docker-compose exec db psql --username=hello_flask --dbname=hello_flask_dev
```

We see our SQL interface:

```
psql (13.1)                                                                                                                                                                      
Type "help" for help. 
```
Checking for a list of databases with "\l"

```
                                        List of databases                                                                                                                        
      Name       |    Owner    | Encoding |  Collate   |   Ctype    |      Access privileges                                                                                     
-----------------+-------------+----------+------------+------------+-----------------------------                                                                               
 hello_flask_dev | hello_flask | UTF8     | en_US.utf8 | en_US.utf8 |                                                                                                            
 postgres        | hello_flask | UTF8     | en_US.utf8 | en_US.utf8 |                                                                                                            
 template0       | hello_flask | UTF8     | en_US.utf8 | en_US.utf8 | =c/hello_flask             +                                                                               
                 |             |          |            |            | hello_flask=CTc/hello_flask                                                                                
 template1       | hello_flask | UTF8     | en_US.utf8 | en_US.utf8 | =c/hello_flask             +                                                                               
                 |             |          |            |            | hello_flask=CTc/hello_flask 
```
Checking for a list of relations with "\dt":

```
          List of relations                                                                                                                                                      
 Schema | Name  | Type  |    Owner                                                                                                                                               
--------+-------+-------+-------------                                                                                                                                           
 public | users | table | hello_flask  
```

### Check Volume Was Created

To check that the volume was created we do:

```
$ sudo docker volume ls
```

VOLUME NAME: postgresloginapiherokudockerflask_postgres_data                                         
```
$ sudo docker volume inspect postgresloginapiherokudockerflask_postgres_data
```
From here we get a result:

```
[                                                                                                                                                                                
    {                                                                                                                                                                            
        "CreatedAt": "2021-02-10T18:55:28-06:00",                                                                                                                                
        "Driver": "local",                                                                                                                                                       
        "Labels": {                                                                                                                                                              
            "com.docker.compose.project": "postgresloginapiherokudockerflask",                                                                                                   
            "com.docker.compose.version": "1.28.2",                                                                                                                              
            "com.docker.compose.volume": "postgres_data"                                                                                                                         
        },                                                                                                                                                                       
        "Mountpoint": "/var/lib/docker/volumes/postgresloginapiherokudockerflask_postgres_data/_data",                                                                           
        "Name": "postgresloginapiherokudockerflask_postgres_data",                                                                                                               
        "Options": null,                                                                                                                                                         
        "Scope": "local"                                                                                                                                                         
    }                                                                                                                                                                            
]  
```
Which shows that we have successfully created the volume.


### Add entrypoint.sh to Verify Postgres Health

Basically, we updated entrypoint.sh which we already had in place.

### Install Netcat

We install Netat and add the entrypoint command on the Dockerfile:

```
# install system dependencies
RUN apt-get update && apt-get install -y netcat
```
This goes at the bottom:

```
# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
```
### Add Environmental Variables

Environmental variables get added to the .env.dev file.

```
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres
```

These are basically placeholders.

After all of this, we can re-build the images and run containers.

1. sudo docker-compose up -d --build
2. visit localhost

It's working the same, but with the specified no email error.

### Add Sample Users, Sample Data

We can add a sample user with the following addition to manage.py

```
@cli.command("seed_db")
def seed_db():
    db.session.add(User(email="test@test123.net"))
    db.session.commit()
```
We run this command with:

```
sudo docker-compose exec web python manage.py seed_db
```
However we get the error:

```
NameError: name 'User' is not defined
```
Not sure why this doesn't work at the moment.

[The Flask Documents on models](https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/) says:

> Generally Flask-SQLAlchemy behaves like a properly configured declarative base from the declarative extension. As such we recommend reading the SQLAlchemy docs for a full reference. However the most common use cases are also documented here.

What's important to realize is where the error is coming from. When diagnosing errors, the first level is to understand, "who" is reporting the error, and then try to solve the error at that level first.  In our case, we look at the code from manage.py:

```
from flask.cli import FlaskGroup

from project import app, db

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
```

Basically, we are in the @cli for Flask. Once we are in this CLI, we are then calling: "session.add" - which appears to be an [SQAlchemy function talked about in the SQAlchemy Documentation](https://docs.sqlalchemy.org/en/14/orm/session_basics.html).  The [Flask CLI documentation](https://flask.palletsprojects.com/en/1.1.x/cli/) which is based upon [Click](https://click.palletsprojects.com/en/7.x/) menntions a few key points:

* the Flask command is installed by Flask, and we have to specify the environment. We can check our .env.dev environmental variable to ensure that this is working.
* We notice that upon logging into the environment using, "Docker Run," we get the following message: "Error: Could not locate a Flask application. You did not provide the "FLASK_APP" environment variable, and a "wsgi.py" or "app.py" module was not found in the current directory."
* We also observe in the Flask CLI documentation a section on, "Custom Commands" which specifies a precise way of creating custom commands using, "Click."

#### FLASK_APP Environment Variable

* One troubleshooting document mentions using "" quotation marks around the app location. This seemed to change nothing.
* [We can go inside of the Docker container](https://stackoverflow.com/questions/34051747/get-environment-variable-from-docker-container/34052766) and run: "echo "$ENV_VAR" to view environmental variables. When we do this, we see nothing.
* [Where are environmental variables stored in linux?](https://stackoverflow.com/questions/532155/linux-where-are-environment-variables-stored) - they are evidently supposed to be stored at /proc/pid/environ, however when we look there, there is no pid.
* According to Docker, [we can set the environmental variables in Compose](https://docs.docker.com/compose/environment-variables/). However, we already have this.
* When we look at the environmental variables stored in /proc/1/environ, we see:

```
HOSTNAME=618d69db60c7
PYTHON_PIP_VERSION=21.0.1
HOME=/root
PYTHONUNBUFFERED=1GPG_KEY=E3FF2839C048B25C084DEBE9B26995E310250568
PYTHONDONTWRITEBYTECODE=1
PYTHON_GET_PIP_URL=https://github.com/pypa/get-pip/raw/4be3fe44ad9dedc028629ed1497052d65d281b8e/get-pip.py
TERM=xtermPATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/binLANG=C.UTF-8
PYTHON_VERSION=3.9.1
PWD=/usr/src/app
PYTHON_GET_PIP_SHA256=8006625804f55e1bd99ad4214fd07082fee27a1c35945648a58f9087a714e9d4
```
All of these variables appear to have been set in the Dockerfile, not docker-compose.yml.

The [Docker Environmental Variables]() documentation mentions:

> The “env_file” configuration option
> You can pass multiple environment variables from an external file through to a service’s containers with the ‘env_file’ option, just like with docker run --env-file=FILE ...:
> web:
>  env_file:
>    - web-variables.env

So, we could try running "docker run --env-file=FILE" to insert the .env.dev file to see what happens.

So we run:

```
sudo docker run \
  -e "FLASK_APP=project/__init__.py" -e "FLASK_ENV=development" \
  --rm -it hello_flask bash
```
Upon doing this, we do not see the "Error: Could not locate a Flask application. You did not provide the "FLASK_APP" environment variable" error.

We can look for environmental variables. If we do, "echo "$ENV_VAR" then nothing comes up, however if we go to proc/1 and cat environ we see the same as above but with these variables added:

```
HOSTNAME=18a00084f5bf
PYTHON_PIP_VERSION=21.0.1
HOME=/rootPYTHONUNBUFFERED=1GPG_KEY=E3FF2839C048B25C084DEBE9B26995E310250568
FLASK_APP=project/__init__.py
PYTHONDONTWRITEBYTECODE=1
PYTHON_GET_PIP_URL=https://github.com/pypa/get-pip/raw/4be3fe44ad9dedc028629ed1497052d65d281b8e/get-pip.py
TERM=xtermPATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
FLASK_ENV=development
LANG=C.UTF-8
PYTHON_VERSION=3.9.1
PWD=/usr/src/app
PYTHON_GET_PIP_SHA256=8006625804f55e1bd99ad4214fd07082fee27a1c35945648a58f9087a714e9d4root
```
Note that FLASK_APP is within that flatfile now.

Going back outside of the runtime without killing it, in a new terminal we can see that we have the same CONTAINER_ID running at no port.

So now if we try to add a seed to the database:

```
sudo docker-compose exec web python manage.py seed_db
```

We still get a, "User is not defined" error. Perhaps this is in part because we are using docker-compose, or because there is another container running.

So what have we established here?  Basically we found that the environmental variables from .env.dev, or at least the ones for FLASK_APP="project/__init__.py" and
FLASK_ENV=development, are not being fed into the Docker container when it is being built.

We can take a look at [this article](https://www.techrepublic.com/article/how-to-use-docker-env-file/) on how to use the .env.dev file. This article mentions that there may be an order of operations on the docker-compose.yml file, in that certain processes can't access the .env.dev file because it's lower down. However it also mentions that by putting, "." at the beginning of the file extension, docker-compose treats it as flat. However we thought we should try it anyway...

```
services:
  web:
    env_file:
      - .env.dev
```

1. sudo docker-compose up -d --build
2. docker-compose exec web python manage.py create_db
3. docker-compose exec web python manage.py seed_db

No errors upon executing the build or create instructions, however the seed_db command still has the, "User is not defined" error.  Let's see if there are any environmental variables in this new container.

```
sudo docker run --rm -it hello_flask bash
```
Here we see that we still have the "You did not provide the FLASK_APP environment variable." So, we can try adding it manually:

```
    environment:
      - FLASK_APP="project/__init__.py
      - FLASK_ENV=development
```
Eliminating...

```
    env_file:
      - .env.dev
```
Now in the logs we see:

```
flask  | Error: Could not import ""project".
```

Note that there was a small typo in the environmental variable with two "" symbols near each other.

And logging into the container itself we still see:

```
Error: Could not locate a Flask application. You did not provide the "FLASK_APP" environment variable, and a "wsgi.py" or "app.py" module was not found in the current directory.
```
So fixing that, and adding additional environmental variables:

```
    environment:
      - FLASK_APP=project/__init__.py
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev
      - SQL_HOST=db
      - SQL_PORT=5432
      - DATABASE=postgres
```

However, we still have the same errors even with this setup.  [This stack overflow comment](https://stackoverflow.com/questions/58578973/docker-compose-not-passing-environment-variables-to-docker-container) takls about how doing a setup with both a Dockerfile and a docker-compose.yml file means that things run in two phases, and that most of the settings in the docker-compose.yml don't have an effect during the build stage, which includes environment variables, network settings and published ports. We also know there is a caching that happens with Docker, and that having a different order of operations may have different builds happen at different times.

Also of note:

* RUN during the build phase means that environment variables will not take effect, it just runs the file.
* CMD will make things get recorded into the image, and then RUN.
* ENTRYPOINT makes getting a debug shell harder, and there is a standard Docker first-time setup pattern that needs ENTRYPOINT for its own purposes. CMD is preferred.

We add the following directly to the Dockerfile and docker-compose build:

```
# system ENV variables
ENV FLASK_APP project/__init__.py
ENV FLASK_ENV development
ENV DATABASE_URL postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev
ENV SQL_HOST db
ENV SQL_PORT 5432
ENV DATABASE postgres
```
This creates different behavior upon logging into the container, there is a constant repeating, "waiting for SQL" error.  However if we take out the SQL variables, and feed in:

```
# system ENV variables
ENV FLASK_APP project/__init__.py
ENV FLASK_ENV development
```
The run "sudo docker run --rm -it hello_flask bash" - the environmental variable problem is gone upon logging into the container.

So now, attempting to seed the database: "sudo docker-compose exec web python manage.py seed_db"

We still get the "NameError: name 'User' is not defined" message. But, at least we eliminated the environmental variable problem.


#### Custom Commands

The [custom commands documentation for Flask](https://flask.palletsprojects.com/en/1.1.x/cli/) is implemented using [Click](https://palletsprojects.com/p/click/) with [full documentation here](https://click.palletsprojects.com/en/7.x/).

Example:

```
import click
from flask import Flask

app = Flask(__name__)

@app.cli.command("create-user")
@click.argument("name")
def create_user(name):
    ...

```
Meanwhile, our manage.py command is:

```
from flask.cli import FlaskGroup
from project import app, db

@cli.command("seed_db")
def seed_db():
    db.session.add(User(email="test@test123.net"))
    db.session.commit()
```
First off, looking at both the Flask CLI and Click documentation, we notice that there is a default "import click" at the top of the function. When we upgrade our requirements.txt file to install click, and add the following:

```
import click
from flask.cli import FlaskGroup
from project import app, db

@cli.command("seed_db")
def seed_db():
  click.echo('hey there thanks for trying to see_db but this is just a dummy function')
```
After trying this out, and rebuilding, we do get an expected message as shown above. So we know for sure that the cli is working. However, User is not being passed for some reason. Reverting back to our database command...

So it appears that, "User" is not being imported.  Thus we add the following to the top of our manage.py file:

```
from project import User
```
After rebuilding, we got a successful outcome.

### Checking the Database Locally

We then follow the following commands in both the terminal and then the SQL command interface to find that we have successfully seeded the database.

```
$ sudo docker-compose exec db psql --username=hello_flask --dbname=hello_flask_dev                                        

psql (13.1)                                                                                                                                                                      
Type "help" for help.                                                                                                                                                            
                                                                                                                                                                                 
hello_flask_dev=# \c hello_flask_Dev                                                                                                                                             
FATAL:  database "hello_flask_Dev" does not exist                                                                                                                                
Previous connection kept                                                                                                                                                         
hello_flask_dev=# \c hello_flask_dev                                                                                                                                             
You are now connected to database "hello_flask_dev" as user "hello_flask".                                                                                                       
hello_flask_dev=# select * from users;                                                                                                                                           
 id |      email       | active                                                                                                                                                  
----+------------------+--------                                                                                                                                                 
  1 | test@test123.net | t 
```

Great!

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

[Importing Models to Flask](https://stackoverflow.com/questions/52409894/cannot-import-app-modules-implementing-flask-cli)
[Structuring Python Applications](https://docs.python-guide.org/writing/structure/)
[Dockerizing Flask with Postgres, Gunicorn and Nginx](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/)
[Flask Mega Tutorial: Logins](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins)
[Flask-Login](https://flask-login.readthedocs.io/en/latest/)