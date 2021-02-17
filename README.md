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

To review the above section, to test out our Docker container along with the freshly written, working code, we can remove all containers and images and then re-build them.

Once images and containers are built, the containers can be shut down, and then restarted again with:

```
sudo docker restart NAME
```

To verify whether the database and the app still, "talk to each other" after restarting we can do the following:

1. sudo docker-compose up -d --build
2. sudo docker-compose exec web python manage.py create_db
3. sudo docker-compose exec web python manage.py seed_db

We can then log back in to the database container specifically via:

4. sudo docker-compose exec db psql --username=hello_flask --dbname=hello_flask_dev 

Query the seeded database:

5. select * from users;

If the expected result comes up, then what you have is reproduceable.

### Production Gunicorn

For production environments, we need a WSGI HTTP server, so we use Gunicorn. This involves:

* Adding gunicorn to the requirements.txt file.
* Adding a command to open gunicorn in a production docker compose file, docker-compose.prod.yml.
* I had already worked on putting together a [Heroku Flask app with Gunicorn here](https://github.com/pwdel/herokudockerflask).

### Production docker-compose.prod.yml

We make some changes to our development docker-compose.yml file, as follows:

```
version: '3.8'

services:
  web:
    image: hello_flask
    container_name: flask
    build: ./services/web
    command: gunicorn --bind 0.0.0.0:5000 manage:app
    ports:
      - 5000:5000
    environment:
      - FLASK_APP=project/__init__.py
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev
      - SQL_HOST=db
      - SQL_PORT=5432
      - DATABASE=postgres
    depends_on:
      - db
  db:
    image: postgres:13-alpine
    container_name: db
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=hello_flask
      - POSTGRES_PASSWORD=hello_flask
      - POSTGRES_DB=hello_flask_dev

volumes:
  postgres_data:
```
Since we are running Guniocorn rather than purely flask, the command: shows launching Guniocorn rather than flask. We also removed volume: from web since it is not needed.

Note that rather than using an .env.prod. file we are just using hard coded environmental variables right here int he code, since it seems to have been a struggle to use a .env file previously. This is something that can be diagnosed seperately in the future as a part of refactoring. Also note that we changed the above environment to, "production."

The database variables are standard user variables which we likely would not like to pass into production, or keep on a server on the web, hence the interest in putting variables into a .env file which can be ignored by a .gitignore.

We would also keep the database variables in an .env.prod.db file, as follows:

```
POSTGRES_USER=hello_flask
POSTGRES_PASSWORD=hello_flask
POSTGRES_DB=hello_flask_prod

```

For production, the best case would actualy be to set those variables as hard-coded variables right on the server itself. However for the purposes of this repo, at least in the Readme file, we will keep them as is for demonstration purposes to show that they are there.

We can then bring down the development containers and attempt to spin up new containers using:

1. docker-compose down -v
2. docker-compose -f docker-compose.prod.yml up -d --build

Checking this at localhost:5000 we should see a sucess Hello World message.

### entrypoint.prod.sh

We create a new entrypoint.prod.sh file which takes out the manage.py file and ends with:

```

if [ "$FLASK_ENV" = "development" ]
then
    echo "Creating the database tables..."
    python manage.py create_db
    echo "Tables created"
fi

exec "$@"
```

Which basically checks if the FLASK_ENV = development, if so then we ...and we update the permissions, and then runs "exec "$@".

We need to make this entrypoint.prod.sh file executable, so we use, "chmod +x services/web/entrypoint.prod.sh"

### Production Dockerfiles

To be able to use the nwe entrypoint.prod.sh, we need a new production dockerfile, Dockerfile.prod.

This is a, "multi-stage build" approach, where an initial image is created for creating Python wheels, then the wheels are copied over and the original builder imgage is disguarded.

Hypothetically, we could have put all of this logic into one single dockerfile for both Dev and Prod.

We also create a non-root user, rather than the default which Docker uses, a root user. This is better for security.

* Add "as builder" to the Python version
* Change to ENV FLASK_ENV production
* Install [flake8 code checker](https://lintlyci.github.io/Flake8Rules/)

```
# lint
RUN pip install --upgrade pip
RUN pip install flake8
COPY . /usr/src/app/
RUN flake8 --ignore=E501,F401 .
```

* flake8 is a modular source code checker.
* Ignoring 501 error (comments) and 401 error
* Ignoring 401 error (multiple imports on one line)

* RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

* pip wheel archives requirements and dependencies. Everything is being archived into requirements.txt.

* create user groups in home folder.
* RUN addgroup -S app && adduser -S app -G app
* putting everything into $APP_HOME
* RUN chown -R app:app $APP_HOME

Finally, we modify our docker-compose.yml file to introduce the new Dockerfile.prod:

web:
  build:
    context: ./services/web
    dockerfile: Dockerfile.prod

## Testing Out on Local Production

We run the following to get things going:

```
$ sudo docker-compose -f docker-compose.prod.yml down -v
$ sudo docker-compose -f docker-compose.prod.yml up -d --build
```
However, we get an error:

ERROR: Service 'web' failed to build

Fortunately, having installed flake8 we now have detailed logs of the build process.

The main error which seems to have caused a problem is:

```
The command '/bin/sh -c flake8 --ignore=E501,F401 .' returned a non-zero code: 1
```
We can try to modify our flake8 command: "RUN flake8 --ignore=E501 ."  However this still resulted in an error, so 


$ sudo docker-compose -f docker-compose.prod.yml exec web python manage.py create_db

### Getting flake8 Working

RUN flake8 --ignore=E501,F401 ./user/src/app

### Getting addgroup and app Working

Create app user, seperate from root.  There are several commands in the Docker file which could be used to do this.

```
RUN addgroup -S app && adduser -S app -G app
```

Change to the app user.
```
USER app
```
Make writable to app user.
```
RUN chown -R app:app $APP_HOME
```

## Pushing to Heroku

We had dealt with this issue previously in the Github Repo on [heroku-docker-flask](https://github.com/pwdel/herokudockerflask).

1. sudo docker login --username=_ --password=$(heroku auth:token) registry.heroku.com

2. heroku create

```
Creating app... done, ⬢ pure-everglades-62431
https://pure-everglades-62431.herokuapp.com/ | https://git.heroku.com/pure-everglades-62431.git
```
3. sudo heroku container:push web --app pure-everglades-62431

When we do this, we get the message, "no images to push."

Whereas in the past we built with, "docker build" we now built this particular project using "docker-compose," therefore we need to use the [heroku docker compose help guide](https://devcenter.heroku.com/articles/local-development-with-docker-compose).

One tip that Docker recommends is to mount our code as a volume, which makes rebuilds unnecessary when code is changed.  This can be done:

```
services:
  web:
    volumes:
      - ./webapp:/opt/webapp

```
...which we have already set for Postgres, but not our source code.

Bascailly, we have to push to the heroku registry, and then release the code from the registry. How do we do this for a specific image?  Here is a reference to [Heroku CLI commands](https://devcenter.heroku.com/articles/heroku-cli-commands).

1. sudo heroku container:login
2. sudo heroku container:push --recursive

When we do this from the /services/web directory, it evidently pushes our Dockerfile to Heroku, however it may not push Dockerfile.prod.

We tried it and it gave a successful result, but then we have to release with:

3. sudo heroku container:release

This gives two options, either:

4. A) sudo heroku container:release web
4. B) sudo heroku container:release web worker

We are not sure which one to use at the moment, so we just picked, "Web"

From here, we got a mesage, "Expected response to be successful, got 404" - however upon looking at Heroku, we see nothing updated.

Instead, we looked at what our production image appeared to be, which looked to be the larger image (since a smaller image got tagged over)

1. $ sudo docker tag 35b4695ba3f3 registry.heroku.com/pure-everglades-62431/web

We then look at images and see there is an image named:

registry.heroku.com/pure-everglades-62431/web

So we then run:

2. $ sudo docker push registry.heroku.com/pure-everglades-62431/web

After running this, we got a bunch of messages saying, "pushed" and a final message:

```
latest: digest: sha256:(long string) size: 2834 
```

So now that we pushed to the registry, we can release it:

$ heroku container:release web

```
Releasing images web to pure-everglades-62431... done

```
If there are multiple images, then you would do, "heroku container:release web worker"

After having pushed the app, we see that there is an application error at:

https://pure-everglades-62431.herokuapp.com/

We get the following log errors:

```
2021-02-12T18:44:19.053709+00:00 heroku[web.1]: State changed from starting to crashed

2021-02-12T18:45:33.913318+00:00 heroku[router]: at=error code=H10 desc="App crashed" method=GET path="/" host=pure-everglades-62431.herokuapp.com request_id=a20a02f8-3251-4b74-886b-87b9828b3edf fwd="207.153.48.94" dyno= connect= service= status=503 bytes= protocol=https

2021-02-12T18:45:34.045732+00:00 heroku[router]: at=error code=H10 desc="App crashed" method=GET path="/favicon.ico" host=pure-everglades-62431.herokuapp.com request_id=b66d927b-2390-42c8-bcab-6d9f1dedfcd7 fwd="207.153.48.94" dyno= connect= service= status=503 bytes= protocol=https
```
We can view the complete [Heroku Error Codes here](https://devcenter.heroku.com/articles/error-codes#h10-app-crashed).

This is likely something to do with whatever the equivalent to the Heroku procfile is in this situation and how gunicorn is serving the app.  Actually, I'm not even sure if the production docker image is using, "docker-compose.prod.yml" and this may take some time to figure out. However, my suspicion is that the following command:

```
$ command: gunicorn --bind 0.0.0.0:5000 manage:app
```

May need to be instead:

```
$ command: gunicorn app:app --log-file=-
```

Basically, this seems to be a Heroku-specific way to get gunicorn going, but we need to test it out.

Another thought - we had essentially deactivated debugging and error codes for production mode by taking out flake8.

### Researching the H10 App Crashed Error

* [Docker Compose Deployment to Heroku Fails](https://stackoverflow.com/questions/61736161/docker-compose-deployment-to-heroku-fails-using-heorku-yml-heroku-at-error-code)
* [Heroku Containerized App Won't Run - Error H10](https://stackoverflow.com/questions/64453383/heroku-containerized-app-wont-run-error-code-h10)
* [Problem on Deploying Docker Image on Heroku](https://stackoverflow.com/questions/62957520/problem-on-deploying-docker-image-on-heroku-react-app)

Notes on the above:

* Stackoverflow users don't find a lot of information to help with this.
* The Heroku Error Codes Docs just say, "H10 - App Crashed - A crashed web dyno or a boot timeout on the web dyno will present this error."
* Further in the docs, error R10 also mentions boot timeout, due to non-port binding.
* So basically, we are told this is either 1) Boot timeout or 2) Regular crash due to something else.

What is a boot timeout and what other types of timeouts are there?

[Wikpedia article](https://en.wikipedia.org/wiki/Timeout_(computing)):

> * Time-out has different meanings. 1. Network parameter, an enforced event designed to occur at the conclusion of an elapsed time. 2. System parameter, an event designed to occur after a time, unless another event occurs first.
> HTTP Connections - web servers save open connections, which consumes CPU time and memory. Timeouts are designed in after about 5 minutes of inactivity.

So somehow, Heroku has built-in timeouts, which likely they set, on their system. What could cause a timeout? Some boot-up process is likely not happening, which is likely Gunicorn.

Without implementing flake8, which we are not even sure will give us more information, we can try playing around with Gunicorn. Alternatively, [there is a way to up the Boot timeout limit for ports on Heroku](https://devcenter.heroku.com/articles/limits#dynos).

What is happening in our gunicorn command?  [Here are the Guniocorn docs](https://docs.gunicorn.org/en/stable/configure.html). 

```
    command: gunicorn --bind 0.0.0.0:5000 manage:app
      ports:
      - 5000:5000
```
#### What is "gunicorn --bind 0.0.0.0:5000 manage:app" Saying?

* [Gunicorn Docs](https://docs.gunicorn.org/en/stable/settings.html) - Gunicorn is a WSGI HTTP server. This means, at a minimum, it understands URL's and the HTTP protocol. It delivers content from the hosted website to the user's device. Basically requests, or the messaging layer, transport layer are done via HTTP messages. These messages include a "message" and a "stream" which includes headers, continuation, and data. Basically it's a layered file that includes all sorts of messaging and port information. We need to be able to feed the right key pices of infomation into that HTTP file, the Host, Port, and message.
* --bind or -b is the socket to bind. "0.0.0.0" means, "whatever port" and then 5000 is the specified port.
* manage:app follows the pattern $(MODULE_NAME):$(VARIABLE_NAME) and in gunicorn is called out as: "$ gunicorn [OPTIONS] APP_MODULE" -- so basically, manage:app is our APP_MODULE.
* The variable name $(VARIABLE_NAME) refers to a WSGI callable that should be found in the specified module. The VARIABLE_NAME can be a function call, in this case, "app" which is a function included in our python application.
* The Wikipedia [WSGI](https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface) artiocle states that it's a Web Server Gateway Interface, and that isa calling convention for web servers to forward requests to web applications or frameworks written in Python. [he standard python documents can be found here](https://www.python.org/dev/peps/pep-3333/) it's basically an interface between Python apps and web servers. 
* So basically, we are going into manage.py and using "app" which refers to the application that has been built and bound together everything in the, "app" module, which includes __init__.py and everything in the project folder.


* [Docker Compose .yml Specification](https://github.com/compose-spec/compose-spec/blob/master/spec.md) 
* "command" overrides the default command declared by the container image (e.g. by the Dockerfile CMD). So we don't have any CMD in our Dockerfile.prod, which means it's not over-riding anything, so this seems to be *the* command specifying the port for Gunicorn to run on.
* We may need to understand a bit more about what our Dockerfile actually does. For example, ["pip wheel"](https://pip.pypa.io/en/stable/reference/pip_wheel/) and [Python Specification on Wheel](https://www.python.org/dev/peps/pep-0427/#abstract) which basically states that Wheel is a Zip-format archive file with the .whl extension which is designed to "zip" up an application before it gets "unzipped" during installation.
* "RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt" seems to take the requirements.txt file and zips it up, whereas "COPY --from=builder /usr/src/app/wheels /wheels COPY --from=builder /usr/src/app/requirements.txt ." evidently unzips the file and extracts it.
* Note in the Docker file there are some other, "User group" points which we commented out. This is something we can go back and fix later, but had worked locally in production mode.
* What about     ports: - 5000:5000 ?   The [docker-compose command line reference](https://docs.docker.com/compose/reference/) and specifically the [reference to docker-compose port](https://docs.docker.com/compose/reference/port/) 
* How do we know to use, "command" vs. "run" in our compose.yml for gunicorn? 


* [Heroku Gunicorn Docs](https://devcenter.heroku.com/articles/python-gunicorn)
* Gunicorn is designed to process HTTP requests concurrently. We could just serve Python up as its own app, but that does not make as much efficient use of dyno resources vs. applications which process one request as a time. Django and Flask include built-in web servers, but those only process a single request at a time.
* I can't find any official documentation on what the official ports are for Heroku and Gunicorn, but some Q&A's reference 8000 rather than 5000.

Ultimately, we need to first see if Gunicorn is even running on our local environment.

1. Log into Docker Container. sudo docker run --rm -it app_name bash
2. Inspect the file structure.

We have:

home/app/web/

Dockerfile Dockerfile.prod entrypoint.prod entrypoint.sh manage.py project requirements.txt

home/app/web/project

__init__.py  __pycache__  config.py

It doesn't seem like we should have Dockerfile and entrypoint.sh in the home/app/web file, so that is a bit confusing.

Side note - in the Dockerfile.prod file, there may be an order of operations problem, in that we start Gunicorn after the environmental variables get set.

So to test out if Gunicorn we can curl http://localhost:5000

root@docker$ apt-get update; apt-get install curl

However, this feeds back an error, perhaps because the http is being served externally rather than internally.

```
curl: (7) Failed to connect to localhost port 5000: Connection refused
```

Internally to our flask app, __init__.py, we see the following line, which specifies port 5000.  This seems to show that Flask is actually serving on port 5000, while Gunicorn may be attempting to serve also on Port 5000.

```
port = int(os.environ.get("PORT", 5000))
```
So that being said, we could have Gunicorn serve on 8000 within Docker, and then try to host on 8000 vs. 5000 and see if it works.

```
    command: gunicorn --bind 0.0.0.0:8000 manage:app
    ports:
      - "8000:8000"
```

So we do a build and then bring the file up with:

```
$ sudo docker-compose -f <production_compose.yml> up -d --build
```

So after doing this, we now see that we have two docker images that were created - the larger one appears to have actually been the intermediary image.  This may have been the problem, that we actually pushed the wrong image, the larger one, to Heroku, rather than the smaller one which is actually serving the app with Gunicorn on port 8000.

| REPOSITORY  | TAG    | IMAGE ID     | CREATED            | SIZE  |
|-------------|--------|--------------|--------------------|-------|
| hello_flask | latest | b7f5050b3cc6 | 38 seconds ago     | 163MB |
| <non>       | <none> | (ID)         | about a minute ago | 228MB |


We push again, using the tag and release methodology, but we still get an app crash.

Interestingly, this [Stack Overflow Article](https://stackoverflow.com/questions/14322989/first-heroku-deploy-failed-error-code-h10) mentions that the PORT gets dynamically assigned by Heroku.

Further, the [Heroku documentation](https://devcenter.heroku.com/articles/dynos#web-dynos) mentions that "A web dyno must bind to its assigned $PORT within 60 seconds of startup."  This implies there is a dynamic, rather than a fixed port, supplied by Heroku.

Looking at [this article on deploying Vue/Flask to Heroku](https://testdriven.io/blog/deploying-flask-to-heroku-with-docker-and-gitlab/#docker), they recommend running the gunicorn command right in the Dockerfile, which looks like this:

```
CMD gunicorn -b 0.0.0.0:5000 app:app --daemon && \
      sed -i -e 's/$PORT/'"$PORT"'/g' /etc/nginx/conf.d/default.conf && \
      nginx -g 'daemon off;'
```
Hypothetically we can translate this same command into our Dockerfile.prod.

[This article on deploying Django to Heroku](https://testdriven.io/blog/deploying-django-to-heroku-with-docker/) mentions using a heroku.yml file with commands, although we didn't need to do that in our previous herokuflask project.  This appears to be something that we use if deploying using Github, it's basically instructions on the build given to Github. The tutorial mentions that commands can be moved from the Dockerfile.yml to the Heroku.yml file, which is basically another form of Dockerfile.

What they show for the Django application is the following:

```
build:
  docker:
    web: Dockerfile
run:
  web: gunicorn hello_django.wsgi:application --bind 0.0.0.0:$PORT
```
So evidently the $PORT variable is [set by Heroku at runtime](https://help.heroku.com/PPBPA231/how-do-i-use-the-port-environment-variable-in-container-based-apps).

```
When deploying a container app on Heroku, we require that Dockerfiles be configured to intake the randomly assigned port on a dyno - exposed as the $PORT environmental variable.

```

So that being said, we take out ports: "8000:8000" and change the following line in our docker-compose.prod.yml file:

```
    command: gunicorn --bind 0.0.0.0:$PORT manage:app
```

Once we did this, then the app did not just immediately crash, but there was a slightly different error.  

Another problem we may have, looking at Heroku is that under our, "Resources" our Dyno command appears to be:

```
 web /home/app/web/entrypoint.prod.sh 
```

#### Checking Entrypoint.sh

We get the following error on the log:

```
2021-02-13T21:57:41.731213+00:00 heroku[web.1]: Starting process with command `/home/app/web/entrypoint.prod.sh`
```
So basically, entrypoint.prod.sh may not be doing anything for us, we would need it to start serving up gunicorn.

CMD vs ENTRYPOINT

CMD -- [Docker Engine CMD Documentation](https://docs.docker.com/engine/reference/builder/) says: 1. There can only be one CMD instruction in a Dockerfile. CMD is used to provide default arguments for the ENTRYPOINT instruction.

ENTRYPOINT - []Docker Documentation on Entrypoint](https://docs.docker.com/engine/reference/builder/#entrypoint) an ENTRYPOINT allows you to configure a container that will run as an executable. So in our case, this is a Postgres entrypoint. ENTRYPOINT will be started as a subcommand of /bin/sh -c, which does not pass signals. The executable will not be the container's PID 1. Only the last ENTRYPOINT in a Dockerfile has effect, much like the CMD instruction.

##### Order of Operatons

Basically, it seems that Heroku expects the Web server to be up and running as a command. However Docker gives an example showing ENTRYPOINT being used prior to CMD. It's reasonable to assume that we first boot up a script which connects us to the database first, and then set up the web server second, and that this will not harm things.

```
# run entrypoint.prod.sh
ENTRYPOINT ["/home/app/web/entrypoint.prod.sh"]

# boot up and run Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT manage:app
```

And with that, the app was successfully deployed.

https://pure-everglades-62431.herokuapp.com/

Interestingly, on the Python command line, we can do:

```
>>> os.listdir("/home/app/web")
['.wh..wh..opq', 'project', '__pycache__', 'manage.py', 'requirements.txt', 'Dockerfile', 'entrypoint.prod.sh', 'Dockerfile.prod', 'entrypoint.sh']
```

However, this dose not allow us to look at the database and make queries.

[Heroku has some Documentation](https://devcenter.heroku.com/articles/dataclips) on how to create, "clips" of data from SQL queries with a tool that they prvodie called [Dataclips](https://data.heroku.com/dataclips/create).

Of course when we run this, using our SQL Query that we had established above,

```
SELECT
  *
FROM
  users
LIMIT 10;
```

We get, 

> ERROR:  relation "users" does not exist LINE 4: users

Basically because we have not set up nor seeded the database. 

## Setup  and Seeding Heroku Database and Making Connection

So what is it that we really want to do?

We want to be able to run the equivalent of two different functions, on Heroku:

1. docker-compose exec web python manage.py create_db
2. sudo docker-compose exec web python manage.py seed_db

So basically, command line create_db and seed_db.

Hypothetically, we should be able to run command line or flask cli through the Heroku CLI or through the Heroku Run function.  What we really need is the Heroku Run function documentation to understand what this really is. Is this the equivalent of the Heroku CLI?

[This article talks about, "User Heroku run commands from Dashboard"](https://devcenter.heroku.com/changelog-items/1137) with even more information linked to [here](https://devcenter.heroku.com/articles/heroku-dashboard). This document in turn refers to the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) as well as the [Platform API](https://devcenter.heroku.com/articles/platform-api-reference). 

Interestingly, at the bottom of the Dashboard, there is a link to the command, "bash."  If we type, "bash" into Heroku run, it pulls is into what appears to be literally the server prompt:

```
bash-5.0$

```
Upon running command, "ls" we get a list of all of the standard folders that we would have seen at the Docker root@docker_id system information.

So from here we might be able to try to run our database inquiry, or rather log into SQL to see if anything happens.

Whereas previously, logging in through docker we had used the command:

```
sudo docker-compose exec db psql --username=hello_flask --dbname=hello_flask_dev                                        
```

Now that we are actually in the server, already logged in we may try th regular psql command:

```
psql --username=hello_flask --dbname=hello_flask_dev
```
When we run this, we see, "psql: command not found"

We can however, run the Python command line. So why not go into the folder where our manage.py file is stored and then run the functions in question?

How do we run class methods from the regular command line?  

1. Create an instance of the class with "test_intance = test(filepath)"
2. Call the Method test_instance.method()

Note, this is different than the Python command line. We were unable to do this from the regular command line, so using the python runtime...

```
So we we enter into Python with python3 then:

>>> import manage as manage
>>> manage.create_db() 

```
So after doing this, we got the message:

Error: Could not locate a Flask application. You did not provide the "FLASK_APP" environment variable, and a "wsgi.py" or "app.py" module was not found in the current directory.

We saw this message before above. Trying to inspect the /proc/1/environ file, we were unable to access this. Doing "echo $ENV_VAR" displays no environmental variables. So presumably, none of our environmental variables have been set up yet within Heroku. We know from previous experience that typically it seems that environmental variables need to be set up manually within Heroku.

Going into our "Settings" within the Heroku dashboard we see there is only one environmental variable set, the DATABASE_URL variable.

What are all of the environmental variables that we need to set within Heroku?

```
From the /proc/1 on our local Production Docker...

* HOSTNAME
* PYTHON_PIP_VERSION=21.0.1
* HOME=/home/app
* GPG_KEY=
* PYTHON_GET_PIP_URL=https://github.com/pypa/get-pip/raw/4be3fe44ad9dedc028629ed1497052d65d281b8e/get-pip.py
* TERM=xterm
* APP_HOME=/home/app/webPATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
* LANG=C.UTF-8
* PYTHON_VERSION=3.9.1
* PWD=/home/app/web
* PYTHON_GET_PIP_SHA256=

From our Dockerfile.prod

* PYTHONDONTWRITEBYTECODE 1
* PYTHONUNBUFFERED 1

* FLASK_APP project/__init__.py
* FLASK_ENV production
* HOME=/home/app
* APP_HOME=/home/app/web

From Our docker-compose.prod.yml

* FLASK_APP=project/__init__.py
* FLASK_ENV=production
* SQL_HOST=db
* SQL_PORT=5432
* DATABASE=postgres
* POSTGRES_USER=hello_flask
* POSTGRES_PASSWORD=hello_flask
* POSTGRES_DB=hello_flask_prod

```

* Note that HOSTNAME is from Docker, it is not needed.
* Note that GPG_KEY above has been taken out, since it is a secure thing we don't want to share on Github.
* PYTHON_GET_PIP_SHA256 has also been taken out, since it is a secure thing.
* Note that our DATABASE_URL is going to be different and assigned by Heroku.
* Also note that FLASK_APP, FLASK_ENV should be the same, because the .prod.yml file simply wasn't populating it on our local machine.
* Also note POSTGRES_USER and POSTGRES_PASSWORD should be changed, these are defaults because we don't want to communicate those on Github.

Once we set all of these variables, then will everything work?

Hypothetically as soon as we set the "DATABASE" variable, then our entrypoint.prod.sh file should be running as a PID process.

```
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi
```

Basically, if we have the DATABASE variable set, then the app should try to connect to SQL_HOST at SQL_PORT.  We can look at the logs for more clues.



```
2021-02-15T16:55:58.132927+00:00 app[web.1]: db: forward host lookup failed: Unknown host

2021-02-15T16:55:58.219708+00:00 heroku[web.1]: Error R10 (Boot timeout) -> Web process failed to bind to $PORT within 60 seconds of launch

2021-02-15T16:55:58.237292+00:00 app[web.1]: db: forward host lookup failed: Unknown host

2021-02-15T16:55:58.304427+00:00 heroku[web.1]: Stopping process with SIGKILL

2021-02-15T16:55:58.456765+00:00 heroku[web.1]: Process exited with status 137

2021-02-15T16:55:58.515476+00:00 heroku[web.1]: State changed from starting to crashed
```

So now, we get an [R10 error rather than an H10 error](https://devcenter.heroku.com/articles/error-codes#r10-boot-timeout).  This is progress. So if the name "db" doesn't work...then what should we use?

### Setting Up Heroku Postgres Variables

1. Under, "Configure Add-ons" we see that there is a Postgres instantiaton.  Clicking on this leads us to: "Datastores > database_name"
2. From here, we see we have the following credentials for manual connections to the database. 

```
Host
Database
User
Port
Password
URI
Heroku CLI
```

From these settings, we can setup the proper environmental variables within our Heroku settings.

```
Host:SQL_HOST
Database: -- Might not match to our code.
User:POSTGRES_USER
Port:SQL_PORT
Password: POSTGRES_PASSWORD
URL:DATABASE_URL
Heroku CLI - Not needed.
```
After we set the above, we then get:

```
021-02-15T17:11:37.408243+00:00 heroku[web.1]: Restarting

2021-02-15T17:11:37.415828+00:00 heroku[web.1]: State changed from up to starting

2021-02-15T17:11:36.789311+00:00 app[api]: Release v32 created by user iotsoftwr3000@gmail.com

2021-02-15T17:11:36.789311+00:00 app[api]: Set POSTGRES_PASSWORD config vars by user iotsoftwr3000@gmail.com

2021-02-15T17:11:38.907408+00:00 heroku[web.1]: Stopping all processes with SIGTERM

2021-02-15T17:11:38.985496+00:00 app[web.1]: [2021-02-15 17:11:38 +0000] [6] [INFO] Worker exiting (pid: 6)

2021-02-15T17:11:39.072782+00:00 heroku[web.1]: Process exited with status 143

2021-02-15T17:11:42.801032+00:00 heroku[web.1]: Starting process with command `/bin/sh -c gunicorn\ --bind\ 0.0.0.0:\8122\ manage:app`

2021-02-15T17:11:45.861684+00:00 app[web.1]: Waiting for postgres...

2021-02-15T17:11:45.876946+00:00 app[web.1]: PostgreSQL started

2021-02-15T17:11:46.380386+00:00 app[web.1]: [2021-02-15 17:11:46 +0000] [5] [INFO] Starting gunicorn 20.0.4

2021-02-15T17:11:46.381216+00:00 app[web.1]: [2021-02-15 17:11:46 +0000] [5] [INFO] Listening at: http://0.0.0.0:8122 (5)

2021-02-15T17:11:46.381385+00:00 app[web.1]: [2021-02-15 17:11:46 +0000] [5] [INFO] Using worker: sync

2021-02-15T17:11:46.397354+00:00 app[web.1]: [2021-02-15 17:11:46 +0000] [6] [INFO] Booting worker with pid: 6

2021-02-15T17:11:47.352601+00:00 heroku[web.1]: State changed from starting to up
```
Which basically seems to say that the database service has started.

Of course, we still don't have any data seeded and no connections made, so we need to log back in, run the, "create_db" and "seed_db" functions to get the dtabase going and seeded.

We once again, enter into the heroku bash via, "bash" then enter into the python3 console.

``` bash
>>> import manage as manage
>>> manage.create_db() 
```
This time, we don't get any errors.

Next, we can inspect the postgres database structure within the pash via:

```
$ db psql --username=hello_flask --dbname=hello_flask_dev 
```

Substituting the username and database name for the names found in our postgres configuration. However, when we try to enter in within, "run" Heroku outputs, "command not found."  That being said, if we look at the database console within the Heroku add-on settings, we can see that there is indeed one table set up.

``` bash
>>> import manage as manage
>>> manage.seed_db() 
```

When we try to run this command, we see that we get an output, "hey this is a test message, thanks for reading!"  We also note that we had mistakenly wrote two functions with the same name for that database initialize function!  So, we have to go back and update the code on our local and redeploy to Heroku.

Once again, to redeploy to Heroku after chaging the code:

1. sudo docker-compose -f docker-compose.prod.yml up -d --build
2. sudo docker tag hello_flask registry.heroku.com/pure-everglades-62431/web
3. sudo docker push registry.heroku.com/pure-everglades-62431/web
4. heroku container:release web

After doing the above and then running manage.seed_db() we now see that there is one row in the postgres database.

We have now successfully connected our database to flask on Heroku.

#### Running Dataclip

Per our discussion above:

```
SELECT
  *
FROM
  users
LIMIT 10;
```

Yields the result: "1 test@test123.net true" which is an expected result.

We also obsverve below that there is an interesting, "schema explorer" below this, showing the datapoints and types for each column.

## Adding Additional Pages to Website

[Adding More Pages to the Website](https://pythonhow.com/adding-more-pages-to-the-website/)

We can follow the recommended [folder structure](https://flask.palletsprojects.com/en/1.1.x/tutorial/layout/) for a flask project.

Create files under /web/project/templates - about.html and home.html.



Add this to the __init__.py file:

```
# run app
@app.route("/")
def home():
  return render_template('templates/home.html')

# route to about page
@app.route('/about/')
def about():
    return render_template('templates/about.html')

```

Re-run Docker with, "sudo docker-compose -f docker-compose.yml up -d --build" using the development version, so that we can view it locally.

When we do this, we get an error, "render_template" is not defined. Basically, we need a render_template function. Evidently [render_template is part of Flask](https://flask.palletsprojects.com/en/1.1.x/api/#flask.render_template). Within our imports at the top of the page we need to do, "from flask import Flask, jsonify, render_template".

After we import this, we then get an error, "TemplateNotFound(template)" for /templates.home.  After playing around with the folder directories and ways of sorting out how this works, we find that we are able to just use the existing folder structure, and simply call out, "home.html" under, "render_template" in order to work, e.g.:

```
# run app
@app.route("/")
def home():
  return render_template('home.html')
```

Now that we have these pages added, we might as well use a Bootstrap stylesheet.  We can download these at [Bootstrap](https://getbootstrap.com/docs/3.3/getting-started/) and add them into our static folder.

However we also found a tutorial which shows how to [add Bootstrap via a jquery script which draws off of bootstrapcdn](https://www.techwithtim.net/tutorials/flask/adding-bootstrap/).  We are deciding to take this route because it's faster.

From this same tutorial, we can also add a sidebar on the home page. So basically, we add a sidebar by adding additional code to the base page, and then updating our various other pages where we want that nav bar to show up, extending the base page.

Note that now that we have the code up and running, there is no need to re-build things from a docker perspective, Docker basically reads from the code that we write.

* As we move along, it is necessary to add some at least extremely basic styling. So we use the documentation about bootstrap from [here](https://getbootstrap.com/docs/3.3/getting-started/). and create some div's that actually create some padding and spacing rather than just having the navbar and text jammed up against the edge of the browser.

Once we create some basic pages, About, Home, Pricing, we are now left with, "Login."

## Login and Logout Functionality

We're going to follow the [tutorial mentioned here](https://pythonbasics.org/flask-login/).  However, this tutorial refers to the MongoDB engine for login/logout, so as a backup, we have [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login) and [this tuorial](https://hackersandslackers.com/flask-login-user-authentication/) as references.clear

First off, it appears that the page, "login.html" within the world of Flask may have a special, pre-defined meaning, basically that it is reserved for a special purpose. When we try to create a login.html page under the /templates folder and link to it, we get a 404 error. We likely need to keep it in the /templates/auth folder.

### Additional Environmental Variables

We add additional environmental variables to the config.py file. We have to remember that we later need to operationalize, or productionize these on Heroku or whatever server we are using as well.

```
    SECRET_KEY = environ.get('SECRET_KEY')

    # Flask-Assets
    LESS_BIN = environ.get('LESS_BIN')
    ASSETS_DEBUG = environ.get('ASSETS_DEBUG')
    LESS_RUN_IN_DEBUG = environ.get('LESS_RUN_IN_DEBUG')

    # Static Assets
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    COMPRESSOR_DEBUG = environ.get('COMPRESSOR_DEBUG')

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

* SECRET_KEY variable is a string used to encrypt all of our user's passwords (or other sensitive information).  We can generate this as a long, non-sensical and impossible to remember character, generating a super long encrypted key using openssl keygen.


### Installing the Module

We find that the most recent version of [Flask-Login](https://pypi.org/project/Flask-Login/) is 0.5.0. so we add this to our requirements.txt.

### Server Binding and Routing

"Server Binding" or "Socket Programming" is a way of connecting two nodes in a network to communicate with each other.  [This tutorial](https://www.tutorialspoint.com/unix_sockets/what_is_socket.htm) describes what sockets are, basically it's a way for computers to talk to each other with standard Unix file descripters, or an integer associated with an open file - a text file, terminal or something else. It's much like a low-level file descripter. Commands such as read(), write() work with sockets in the same way they do with files and pipes. FTP, SMTP and POP3 make use of sockets.

We find the latest [Flask-Login](https://flask-login.readthedocs.io/en/latest/) version there.

We add this to the requirements file, and our Dockerfile takes care of the pip installation.

The two main things that we can do to get flask_login set up in terms of importing are:

```
from flask_login import LoginManager
login_manager = LoginManager()
```

There is a minimum number of activities needed to set up a Flask login, which include:

* Construct the core app object
* Configuration
* Initialize Plugins
* Register blueprints
* Create database models
* Compile static assets.

All of the above can be put into a function called, "create_app" which can be called at the start. Whereas perviosly we used the function create_db, we can instead put the above set of activities in a function, which can go in the __init__.py file.

The [hackers and slackers tutorial]() that we are reading gives the following 

```
def create_app():
    """Construct the core app object."""
    app = Flask(__name__, instance_relative_config=False)

    # Application Configuration
    app.config.from_object('config.Config')

    # Initialize Plugins
    db.init_app(app)
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
```
We have to adapt this to our own program, which involves docker and some standards which are in place to allow the app to work.

* auth_bp is imported from auth.py, and our “main” application routes are associated with main_bp from routes.py

We can build this in docker, and run this in development mode to see what kinds of errors we get.

So after we build and then check the docker-compose logs, as expected for the line, "db = SQLAlchamey(app)" we get "NameError: name 'app' is not defined."

So the first thing we needed to do is change db so that it does not require (app) as an argument.

```
# activate SQLAlchemy
db = SQLAlchemy()
# set login manager name
login_manager = LoginManager()
```

Next, we needed to define app in order to pass it over to @app.route("/").  So we tried to define app = create_app(). However we get the error:

```
flask  |   File "/usr/src/app/project/__init__.py", line 26, in create_app
flask  |     from . import routes
flask  | ImportError: cannot import name 'routes' from partially initialized module 'project' (most likely due to a circular import) (/usr/src/app/project/__init__.py)
```

The reason for the inability to import "routes" comes from this line in the code:

```
    with app.app_context():
        from . import routes
        from . import auth
        from .assets import compile_assets
```
* [app_context](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.app_context) is actually a native app module, so there is no problem picking that function up. app_context() makes current_app() point at this application.
* [blueprints](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.blueprints) is also a native flask plugin. Blueprints, which are essentially the Flask equivalent of Python modules, in that they encapsulate feature-size sections of the application, such as user auth, profiles, etc.

We need to understand more about how the Python import system works. What does it mean to use "from ." ?  This is what is known as a [Relative Import](https://docs.python.org/3/reference/import.html#package-relative-imports). 

> Two or more leading dots indicate a relative import to the parent(s) of the current package, one level per dot after the first. For example, given the following package layout:

```
package/
    __init__.py
    subpackage1/
        __init__.py
        moduleX.py
        moduleY.py
    subpackage2/
        __init__.py
        moduleZ.py
    moduleA.py
```
The following are valid:

```
from .moduleY import spam
from .moduleY import spam as ham
from . import moduleY
from ..subpackage1 import moduleY
from ..subpackage2.moduleZ import eggs
from ..moduleA import foo
```
So basically saying, "from . import X" is like saying, "anywhere in the containing folder above, import X.py"

Basically this means we need the following:

* assets.py
* auth.py
* forms.py
* models.py
* routes.py

And they should all be within the project folder, like so:

```
├── /project
│   ├── __init__.py
│   ├── assets.py
│   ├── auth.py
│   ├── config.py
│   ├── forms.py
│   ├── models.py
│   ├── routes.py
│   ├── /static
│   └── /templates
```
What goes in these python files and what do they do?

#### routes.py

This protects parts of our app from unauthorized users.  Here's what we put in routes.py:

1. We have to define two blueprints - main_bp and home_bp. Blueprints help standardize how everything is laid out in terms of routes and templates, basically our folder structure.
2. We then use .route to return templates from index.jinja2, dashboard.jinja2 and also a logout.

Given this, we have to make sure we have these templates available in our /templates folders.


Basically, this renders a template which gives a login message to the user on the main page, '/'. There is no static page that is used, but rather it writse it out on teh login page.

There is also a logout route.

Since we are dealing with route.by, we also must take note that the tutorial overall does discuss different forms of routing within the [Blueprint tutorial](https://hackersandslackers.com/flask-blueprints/).  This also includes the definition of a home() function.

This harkens back to our __init__.py function, which has the line:

```
        # Register Blueprints
        app.register_blueprint(home.home_bp)
```

This of course also entails importing a route from our "home" or rather, "project" folder.  We put this at the top of __init__.py

```
from .project import routes
```

#### auth.py

[Per this tutorial here](https://hackersandslackers.com/flask-assets/), we have two sections of the auth.py file:

* @auth_bp.route('/signup', methods=['GET', 'POST'])
* @auth_bp.route('/login', methods=['GET', 'POST'])

Basically, a signup and a login.

##### Signup

1. We start out with a blueprint.
2. Signing up - the signup route handles GET requests when users land on the page for the first time, and POST when they attempt to submit the signup form.
3. The route checks all cases of a user attempting to sign in by checking the HTTP method via flask's request object. If the user is arriving for the first time, the route serves the signup.jinja2 template via [render_template()](https://flask.palletsprojects.com/en/1.1.x/api/#flask.render_template).
4. So first auth.py validates if the user filled out the form correctly with the [built in flask-WFT method form.validate_on_submit()](https://flask-wtf.readthedocs.io/en/stable/quickstart.html#validating-forms). This will only trigger if the incoming request is a POST containing form information.
5. We verify that the user isn't an existing user.
6. Create a user via the User model.
7. Add user to database.
8. login_user() is a method from the [flask_login package](https://flask-login.readthedocs.io/en/latest/#flask_login.login_user)
9. Finally everything is redirected via "return redirect(url_for()".

##### Login

1. Uses pretty much the same logic.
2. Does user.check_password() - which appears to come from the werkzeug library, however it appears to possibly be: [check_password_hash](https://werkzeug.palletsprojects.com/en/1.0.x/utils/?highlight=check_password#werkzeug.security.check_password_hash) which is different than check_password. set_password() and check_password() are both from the werkzeug library according to our tutorial.
3. Redirect.

###### Login Helpers

* user_loader checks to make sure user is still logged in.
* unauthorized handler sends unauthorized users away.

#### assets.py

The assets are basically the CSS, 

[Per this tutorial here](https://hackersandslackers.com/flask-assets/), we have two sections of the 

###### Jinja2 Templates



#### forms.py

signup.jinja2

login.jinja2



#### models.py



### User Model

We refer to login_view as "login," within this __init__.py file. This is routed below as an @app.route with the following logic:

```
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
```

#### User Model

Our user model is not sufficient.  Basically our current user model looks like the following:

```
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    def __init__(self, email):
        self.email = email
```

This only includes an id, email and reference to whether it's active or not.  We need to add the following properites:

* is_authenticated: The current user is authorized because we can operate when we log on, so the default is the authorized
* is_anonymous: it is obvious that if the current user is anonymous, it must not be
* is_active: for judging whether the current user has been activated, the activated user can log on to
* get_id: returns the id. But we still cannot know who the current login user is, so we also need to tell Flask-Login how to obtain the user’s method through an id:


```
class User(db.Document):   
    name = db.StringField()
    password = db.StringField()
    email = db.StringField()                                                                                                 
    def to_json(self):        
        return {"name": self.name,
                "email": self.email}

    def is_authenticated(self):
        return True

    def is_active(self):   
        return True           

    def is_anonymous(self):
        return False          

    def get_id(self):         
        return str(self.id)
```

We then need a login manager, which is able to query who the current login user us, so there fore we can judge whether they are able to login or not.

```
@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()
```

## Debugging

### login_manager

After adding auth.py, config.py, routes.py and models.py we have an error saying that "NameError: name 'login_manager' is not defined" on the auth.py page.  This was because we had to add, "from . import login_manager" at the top of auth.py, along with other imports.

### ModuleNotFoundError: No module named 'flask_wtf'

After adding auth.py, config.py, routes.py and models.py we have an error saying that:

File "/usr/src/app/project/forms.py", line 2, in <module>
flask  |     from flask_wtf import FlaskForm
flask  | ModuleNotFoundError: No module named 'flask_wtf'

This was because we needed to add "Flask-WTF==0.14.3", the most recent version to the requirements.txt form.

```
from flask_wtf import FlaskForm
```
### Exception: Install 'email_validator' for email validation support.

email_validator is actually [its own module](https://pypi.org/project/email-validator/), so we need to install this on the requirements.txt file.

```
from wtforms import email_validator
```
### ModuleNotFoundError: No module named 'flask_assets'

[flask_assets is its own module](https://pypi.org/project/Flask-Assets/) which we have to install on requirements.txt and import.

under __init__.py and assets.py

```
from flask_assets import Environment, Bundle
```

The tutorial we are following refers to the [folder structure](https://hackersandslackers.com/flask-assets/) and potentially needing to rename the folders to align with this module.

### ImportError: cannot import name 'compile_assets' from 'project.assets' (/usr/src/app/project/assets.py)

This appears to have meant to import the functon compile_static_assets.

from .assets import compile_static_assets

There is and was no compile_assets function.

### 

Within __init__.py, after starting up, the function db.create_all() tries to run, and theere is no database:

flask  |   File "/usr/src/app/project/__init__.py", line 39, in create_app
flask  |     db.create_all()

Through the errors we see:

flask  | sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL:  database "hello_flask_dev" does not exist

flask  | (Background on this error at: http://sqlalche.me/e/13/e3q8)

[On the SQLAlchemy docs](https://docs.sqlalchemy.org/en/13/errors.html#error-e3q8) they mention:

> The OperationalError is the most common (but not the only) error class used by drivers in the context of the database connection being dropped, or not being able to connect to the database. For tips on how to deal with this, see the section Dealing with Disconnects.

Basically, we don't know what the function "create_all()" is trying to do with the database, or if it even does anything at this point.

Looking at the [documentation on create_all for SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/#flask_sqlalchemy.SQLAlchemy.create_all), we see that this is simply a built-in function desigend to create all tables.

We had used this previously under, "manage.py" as follows:

> @cli.command("create_db")
> def create_db():
>    db.drop_all()
>    db.create_all()
>    db.session.commit()

However, it may not be that we need to expand upon this definition, it may be that our database "hello_flask_dev" may literally no longer exist anymore.

We know from experience that the docker-compose.yml does not tend to do well with environmental variables.  Currently it is our docker-compose.yml file which sets the database environment.

```
  db:
    image: postgres:13-alpine
    container_name: db
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=hello_flask
      - POSTGRES_PASSWORD=hello_flask
      - POSTGRES_DB=hello_flask_dev
```
However we may need to move these environmental variables to the Dockerfile itself.  When we log in as follows, we get a, "hello_flask_dev" does not exist message.


```
sudo docker-compose exec db psql --username=hello_flask --dbname=hello_flask_dev
```
Adding the following to the Dockerfile:

```
      - POSTGRES_USER=hello_flask
      - POSTGRES_PASSWORD=hello_flask
      - POSTGRES_DB=hello_flask_dev
```
After doing this, we still get a database "hello_flask_dev" does not exist error.

Could it be the order of operations on the __init__.py file?

Curiously, we see that we get the following upon initiation of the db:

```
db     | 2021-02-17 12:01:30.806 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db     | 2021-02-17 12:01:31.399 UTC [20] LOG:  database system was shut down at 2021-02-17 12:01:24 UTC
```

As well as:

```
db     | 2021-02-17 12:01:31.577 UTC [1] LOG:  database system is ready to accept connections
db     | 2021-02-17 19:20:02.579 UTC [485] FATAL:  database "hello_flask_dev" does not exist
db     | 2021-02-17 19:20:03.384 UTC [486] FATAL:  database "hello_flask_dev" does not exist
db     | 2021-02-17 19:43:53.883 UTC [517] FATAL:  database "hello_flask" does not exist
db     | 2021-02-17 19:44:30.052 UTC [523] FATAL:  database "hello_flask" does not exist
db     | 2021-02-17 19:44:32.238 UTC [530] FATAL:  database "hello_flask_dev" does not exist
db     | 2021-02-17 19:48:51.822 UTC [536] FATAL:  database "hello_flask_dev" does not exist
db     | 2021-02-17 19:48:52.622 UTC [537] FATAL:  database "hello_flask_dev" does not exist

```
Which seems to imply that the database is switching back and fourth between names.

There is a comment on the tutorial:

> Thanks for the great tutorials! Following your app structure, I was getting the error: "sqlalchemy.exc.operationalerror (sqlite3.operationalerror) no such table" I solved it by importing the model classes just before "db.createall()" in myinit.py, inside "app.appcontext()" from .models import Model1, Model2 db.create_all() is this the proper solution, or would you recommend another way around that?

So basically, we may need to import the model classes before creating the database.  Which, this makes sense because previously we had created our simple model class as follows, before accessing the create_db through the flask cli on manage.py.

```

# insert database model class
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    def __init__(self, email):
        self.email = email

```

Hence, we insert:

```
        # import model class
        from . import models

        # Create Database Models
        db.create_all()
```

Of course, this does not work, and we get the same error. It could be that we are trying to connect to the database twice, so we may need to remove any other database code that we had created previously to see if anything happens. We may also need to delete any currently existing database within Docker to make sure it restarts properly.

We remove:

```
# insert database model class
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    def __init__(self, email):
        self.email = email
```

...which did nothing, but it's OK because we needed a new user model anyway from our new file.

Finally we found from looking at our previous tutorial, that if you get the following error;

"sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
FATAL:  database "hello_flask_dev" does not exist"

Then you just need to run:

```
docker-compose down -v
```
...to remove the volumes along with the containers. Then, re-build the images, run the containers, and apply the migrations. Basically, this gets rid of all of our previous baggage so we can start fresh.

### KeyError: 'FLASK_ENV'

Here we are simply getting a key error referecing our config.py file.

```
flask  |   File "/usr/src/app/project/__init__.py", line 45, in create_app
flask  |     if app.config['FLASK_ENV'] == 'development':

```

We had not set our FLASK_ENV within the configuration file, we had set it within the Dockerfile, so we can do a quick hack to see if we can clear it by setting FLASK_ENV to development in config.py.

This does not work, however thinking about things further - really our app configuraton happens as a function of the environment, and we don't want to hard code anything.

It seems that we simply would like to go forward with, "compile_static_assets" in any case - however what does this do, really?

When we delete the conditional, everything with the database boots up and appears to work flawlessly.

Can we inspect the database?

We can log in via the standard method, and inspect the database with SQL commands \l, \dt and sofourth.

We did this and found a description of the database exactly as we had expected:

```
                                         Table "public.flasklogin-users"                                                                                                                    
   Column   |            Type             | Collation | Nullable |                    Default                                                                                               
------------+-----------------------------+-----------+----------+------------------------------------------------                                                                          
 id         | integer                     |           | not null | nextval('"flasklogin-users_id_seq"'::regclass)                                                                           
 name       | character varying(100)      |           | not null |                                                                                                                          
 email      | character varying(40)       |           | not null |                                                                                                                          
 password   | character varying(200)      |           | not null |                                                                                                                          
 website    | character varying(60)       |           |          |                                                                                                                          
 created_on | timestamp without time zone |           |          |                                                                                                                          
 last_login | timestamp without time zone |           |          |                                                                                                                          
Indexes:  
```

### AttributeError: 'Flask' object has no attribute 'register'

Next, we are lacking some assets within our file, assets.py.

```
flask  |   File "/usr/src/app/project/assets.py", line 32, in compile_static_assets
flask  |     assets.register('main_styles', main_style_bundle)
flask  | AttributeError: 'Flask' object has no attribute 'register'
```
This is a part of, "assets" and there is a [whole seperate tutorial on flask-assets](https://hackersandslackers.com/flask-assets/).

#### Install Flask Assets

We talked about this above, and have installed it in requirements.txt.

However we also need to install:

* lesscpy
* cssmin
* jsmin

Within our config.py file, we add:

LESS_BIN = '/usr/local/bin/lessc'
ASSETS_DEBUG = False
ASSETS_AUTO_BUILD = True


## Password Hashing

https://flask-bcrypt.readthedocs.io/en/latest/

## Flask Login Library

https://flask-login.readthedocs.io/en/latest/

## User Model

https://flask-user.readthedocs.io/en/latest/data_models.html




## User Registration

https://dev.to/imdhruv99/flask-login-register-logout-implementation-3hep


## Webforms on Flask

https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms


## Pushing Everything to Production

We need to set these variables to put everything into production, including the login capabilities.

```
    SECRET_KEY = environ.get('SECRET_KEY')

    # Flask-Assets
    LESS_BIN = environ.get('LESS_BIN')
    ASSETS_DEBUG = environ.get('ASSETS_DEBUG')
    LESS_RUN_IN_DEBUG = environ.get('LESS_RUN_IN_DEBUG')

    # Static Assets
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    COMPRESSOR_DEBUG = environ.get('COMPRESSOR_DEBUG')

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```


## Conclusion

Thoughts:

* PORTS, defaulting to blank, different production environments.
* Multi-stage builds, zipping files to be able to more easily pass to production
* Uselessness of the docker-compose.yml and docker-compose.prod.yml file versus the Dockerfile and Dockerfile.prod themselves.
* Adaptable Dockerfile for both Production and Dev, depending upon command sent...rather than different dockerfiles?  Or is it just the YML file?
* What do the YML files really do anyway?  They don't seem to have much control over the situation.
* How do we prevent dockerfiles from being copied over into the production environment?  Does that matter?
* Do environmental variables always need to be set manually within Heroku?  If so why?  Is this more secure?
* What is the GPG key?
* When do we need to rebuild Docker and when can we hold off? Is it only for static pages or is it for any functions as well?

Future Work

* Refactoring code, putting initialization into diffrent functions and classes
* Getting flake8 working.
* Getting this working: # RUN addgroup -S app && adduser -S app -G app
* SECRET_KEY, DEBUG, and ALLOWED_HOSTS 
* Redis for database concurrent connections, if in fact we get a lot of activity on the app.
* Installing Bootstrap locally, rather than grabbing from CDN
* Migrating data without losing the data

Flask Bootstrap - serve from a CDN. https://pythonhosted.org/Flask-Bootstrap/

https://pythonhosted.org/Flask-Bootstrap/basic-usage.html#sample-application

https://flask-menu.readthedocs.io/en/latest/

https://pythonhow.com/flask-navigation-menu/

Flask CSS 

https://pythonhow.com/add-css-to-flask-website/

NGinx

Static Content


## References

* [Flask Assets Tutorial](https://hackersandslackers.com/flask-assets/)
* [Flask Login Python Basics](https://pythonbasics.org/flask-login/).
* [Setting up Postgres, SQLAlchemy, and Alembic](https://realpython.com/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/)
* [Deploying Django to Herokku with Docker](https://testdriven.io/blog/deploying-django-to-heroku-with-docker/)
* [Deploying Flask to Heroku with Docker and Gitlab](https://testdriven.io/blog/deploying-flask-to-heroku-with-docker-and-gitlab/#docker)
* [Importing Models to Flask](https://stackoverflow.com/questions/52409894/cannot-import-app-modules-implementing-flask-cli)
* [Structuring Python Applications](https://docs.python-guide.org/writing/structure/)
* [Dockerizing Flask with Postgres, Gunicorn and Nginx](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/)
* [Flask Mega Tutorial: Logins](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins)
* [Flask-Login](https://flask-login.readthedocs.io/en/latest/)