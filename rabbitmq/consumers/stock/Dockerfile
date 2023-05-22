FROM python:3.11-slim-buster AS builder

WORKDIR /home/flask-app

# gcc is only needed to install psycopg2.
RUN apt-get update && \
    apt-get install -y libpq-dev gcc

COPY . .

RUN pip install -r requirements.txt

