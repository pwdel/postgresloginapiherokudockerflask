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
4. 

## References

[Dockerizing Flask with Postgres, Gunicorn and Nginx](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/)
[Flask Mega Tutorial: Logins](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins)
[Flask-Login](https://flask-login.readthedocs.io/en/latest/)