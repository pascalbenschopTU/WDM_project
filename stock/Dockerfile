FROM python:3.11-slim-buster

WORKDIR /home/flask-app

RUN apt-get update && \
    apt-get install -y libpq-dev gcc

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000