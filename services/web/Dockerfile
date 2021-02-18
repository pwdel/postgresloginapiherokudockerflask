# set base image (host OS)
FROM python:3.9-slim-buster

# set the working directory in the container
WORKDIR /usr/src/app

# set environment variables---------------------
# prevent python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE 1

# prevent python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# system ENV variables
ENV FLASK_APP project/__init__.py
ENV FLASK_ENV development
ENV SECRET_KEY 'whatever'

# install system dependencies
RUN apt-get update && apt-get install -y netcat

# install NPM to be able to install less
RUN apt-get install -y npm
# globally install less
RUN npm install less -g

# install dependencies
RUN pip install --upgrade pip

# copy the content of the local src directory to the working directory
COPY ./requirements.txt /usr/src/app/requirements.txt

# install requirements
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]