import os
import atexit
from typing import List
from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pika
import uuid
import psycopg2
import random
import string

app = Flask("stock-service")
api_identifier = "xyzasd"

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
big_db = "big_db_stock_requests"
channel.queue_declare(queue=big_db, durable=True)
channel.queue_declare(queue=api_identifier, durable=True)
channel.queue_declare(queue="new_stock", durable=True)
channel.exchange_declare(exchange='new_items', exchange_type='fanout')


connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)

def close_db_connection():
    pass
    # engine.close()

atexit.register(close_db_connection)

@app.post('/item/create/<price>')
def create_item(price: int):
    price = int(price)
    characters = string.ascii_uppercase + string.digits
    # Generate a random string of length 8
    item_id = ''.join(random.choices(characters, k=8))
    message = f"{item_id},{price}"
    channel.basic_publish(exchange='new_items', routing_key='', body=message)
    item = {'item_id': item_id, 'price': price, 'stock': 0} #: dict[str, int]
    return item, 201


@app.get('/find/<item_id>')
def find_item(item_id: str):
    with engine.connect() as db_connection:
        statement = text("SELECT * FROM stock WHERE id = :id")
        result = db_connection.execute(statement, {"id": item_id})
        for row in result:
            item = {'item_id': row[0], 'price': row[1], 'stock': row[2]}
            return item, 200
    return "Couldn't find item", 404
        


@app.post('/add/<item_id>/<amount>')                                                                                                                                                                                                                                                                                                                   
def add_stock(item_id: str, amount: int):
    channel.basic_publish(exchange='',
                            routing_key="new_stock",
                        body=f"{item_id},{amount}")
    return "Success", 200


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    with engine.connect() as db_connection:
        statement = text("UPDATE stock SET stock = stock - :amount WHERE id = :item_id AND stock > 0;")
        result = db_connection.execute(statement, params={"item_id": item_id, "amount": amount})
        if result.rowcount < 1:
            return "Not enough stock", 400
        return "Success", 200

@app.post('/subtract_bulk/<item_ids>')
def decrement_stock_bulk(item_ids: str):
    ids = item_ids.split(",")
    with sessionmaker(bind=engine) as session:
        try:
            # Check if all stock counts are above 0.
            statement = text("SELECT * FROM stock WHERE id = ANY(:ids) AND stock > 0 FOR UPDATE;")
            items = session.execute(statement, params={"ids": ids})
            # if it's above 0, it isn't possible for all of them
            for item in items:
                id = item["id"]
                stock = item["stock"]
                if stock <= 0:
                    ## post message that we need more stock
                    channel.basic_publish(exchange='',
                        routing_key=big_db,
                    body=f"{api_identifier},{id}")
                    ## release transaction
                    return f"Not enough of {id}", 400
                # If all amounts are above 0, decrement them by 1
                update_statement = "UPDATE stock SET stock = stock - 1 WHERE id = ANY(:ids) AND stock > 0;"
                session.execute(update_statement,  {"ids": ids})
        except psycopg2.Error as e:
                # Handle any errors that occur during the transaction
            return "Something went wrong", 400
    return f"{api_identifier}", 200