FROM python:3.11-slim-buster

WORKDIR /home/stock-consumer

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN pip install -r requirements.txt

