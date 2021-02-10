# set base image (host OS)
FROM python:3.9-slim-buster

# set the working directory in the container
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip

# copy the content of the local src directory to the working directory
COPY ./requirements.txt /usr/src/app/requirements.txt

# install requirements
RUN pip install -r requirements.txt

# use entrypoint.sh as entrypoint
# ENTRYPOINT ["/app/entrypoint.sh"]

# command to run on container start
CMD [ "python", "./server.py" ] 