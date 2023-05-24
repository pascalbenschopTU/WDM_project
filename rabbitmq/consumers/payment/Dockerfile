FROM python:3.11-slim

WORKDIR /home/payment-consumer

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .