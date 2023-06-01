import os
from flask import Flask, request
from sqlalchemy import create_engine, text
import pika
import random
import string
import time
import logging
from RabbitMQClient import RabbitMQClient
app = Flask("stock-service")
logging.basicConfig(level=logging.INFO)
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
channel.exchange_declare(exchange='new_items', exchange_type='fanout', durable=True)
channel.exchange_declare(exchange='subtract', exchange_type='fanout', durable=True)
channel.exchange_declare(exchange='add', exchange_type='fanout', durable=True)

connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
## We do reads directly, and we allow dirty reads.
engine = create_engine(connection_string)

@app.post('/item/create/<price>')
def create_item(price: int):
    price = int(price)
    ## TODO fix this thing
    characters = string.ascii_uppercase + string.digits
    # Generate a random string of length 8
    item_id = ''.join(random.choices(characters, k=8))
    message = f"{item_id},{price}"
    channel.basic_publish(exchange='new_items', routing_key='', body=message)
    item = {'item_id': item_id, 'price': price, 'stock': 0}
    return item, 201

@app.get('/find/<item_id>')
def find_item(item_id: str):
    with engine.connect().execution_options(isolation_level="READ UNCOMMITTED") as db_connection:
        statement = text("SELECT * FROM stock WHERE id = :id")
        result = db_connection.execute(statement, {"id": item_id})
        for row in result:
            item = {'item_id': row[0], 'price': row[1], 'stock': row[2]}
            return item, 200
    return "Couldn't find item", 404

@app.post('/add/<item_id>/<amount>')                                                                                                                                                                                                                                                                                                                  
def add_stock(item_id: str, amount: int):
    channel.basic_publish(exchange='add',
        routing_key="",
        body=f"{int(time.time())},{item_id},{amount}")
    return "Success", 200

@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    client = RabbitMQClient(connection, "subtract")
    response = client.call(f"{int(time.time())},{item_id},{amount}")    
    return response, 200
    # if response == "Success":
    #     return "Success", 200
    # return "Not enough stock", 400

@app.post('/subtract_bulk')
def decrement_stock_bulk():
    data = request.get_json()
    ids = data['ids']

    client = RabbitMQClient(connection, "subtract")
    message = f"{time.time()},{client.callback_queue},"
    for id in ids:
        message += f"{id},1,"
    
    response = client.call(message[:-1])
    if response == "Success":
        return "Success", 200
    return "Something went wrong", 400
