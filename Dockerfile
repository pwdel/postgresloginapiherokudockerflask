# set base image (host OS)
FROM python:3.9-slim-buster

# set the working directory in the container
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy the dependencies file to the working directory
COPY app/requirements.txt .

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY app/src/ .

# use entrypoint.sh as entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# command to run on container start
# CMD [ "python", "./server.py" ] 