from flask import Flask, request
import pika
import random
import string
import logging
import uuid
from RabbitMQClient import RabbitMQClient
app = Flask("stock-service")
logging.basicConfig(level=logging.INFO)
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
exchange_name = "requests"
channel.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=True)
channel.exchange_declare(exchange='new_items', exchange_type='fanout', durable=True)

@app.post('/item/create/<price>')
def create_item(price: int):
    price = int(price)
    item_id = str(uuid.uuid4())
    message = f"{item_id},{price}"
    channel.basic_publish(exchange='new_items', routing_key='', body=message)
    item = {'item_id': item_id, 'price': price, 'stock': 0}
    return item, 201

@app.get('/find/<item_id>')
def find_item(item_id: str):
    client = RabbitMQClient(connection, exchange_name)
    response = client.call(f"select,{item_id}")
    parsed_response = response.split("status:")
    return parsed_response[0], parsed_response[1]


@app.post('/add/<item_id>/<amount>')                                                                                                                                                                                                                                                                                                                  
def add_stock(item_id: str, amount: int):
    channel.basic_publish(exchange=exchange_name,
        routing_key="", body=f"add,{item_id},{amount}")
    return "Success", 200

@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    client = RabbitMQClient(connection, exchange_name)
    response = client.call(f"subtract,{item_id},{amount}")    
    if response == "Success":
        return response, 200
    return response, 400

@app.post('/subtract_bulk')
def decrement_stock_bulk():
    data = request.get_json()
    ids = data['ids']
    client = RabbitMQClient(connection, exchange_name)
    message = "subtract,"
    for id in ids:
        message += f"{id},1,"
    # removes the last,
    response = client.call(message[:-1])
    if response == "Success":
        return "Success", 200
    return "Something went wrong", 400
