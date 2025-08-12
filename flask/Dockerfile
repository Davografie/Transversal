# https://runnable.com/docker/python/dockerize-your-flask-application
FROM python:3.9.6-slim-buster

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt
