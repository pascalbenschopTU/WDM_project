import os
import atexit

from flask import Flask
import redis
import pika

app = Flask("stock-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/item/create/<price>')
def create_item(price: int):
    item_id = db.incr('item_id')
    item = {'item_id': item_id, 'price': price, 'stock': 0}
    db.hset(f'item:{item_id}', mapping=item)

    return item, 201


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item = db.hmget(f'item:{item_id}', 'price', 'stock')
    if None in item:
        return None, 404

    return {'item_id': item_id, 'price': int(item[0]), 'stock': int(item[1])}, 200


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    db.hincrby(f'item:{item_id}', 'stock', int(amount))
    return "Success", 200


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    stock = db.hget(f'item:{item_id}', 'stock')
    if int(stock) < int(amount):
        return "Not enough stock", 400
    else:
        db.hincrby(f'item:{item_id}', 'stock', -int(amount))
        return "Success", 200

## define channels
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
## Forwards to stock.
channel.queue_declare(queue=os.environ['order_stock'], durable=True)
## Recieves ok from payment if withdrawl was ok
channel.queue_declare(queue=os.environ['stock_payment'], durable=True)
## recieves messages from stock if not in order

## TODO if any errors in any of them we drop it.
## Have to be atomic, if errors occour we also don't post the message to payment
def decrement(params, items):
    total_price = sum([item.price for item in items])
    paymentmessage = f"{params[0]},{params[1]},{total_price}"
    channel.basic_publish(
        exchange='',
        routing_key=os.environ['order_payment'],
        body=paymentmessage,
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
    ))

def order_callback(ch, method, properties, body):
    params = body.decode().split(",")
    items = []
    for i in range(3, len(params)):
        item = find_item(params[i])
        if not item: ## TODO is this valid python?
            message = f"False,stock" ## if not in, we post back to the order it wasn't in stock
            channel.basic_publish(
                exchange='',
                routing_key=params[0],
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ))
            return
        items.append(item)

    if params[2] == "dec":
        decrement(params, items)
    else:
        ## increment stock
        ## Don't know if we should perhaps acknowledge this or something.
        ## we will figure that out later
        pass

channel.basic_consume(queue=['order_stock'], on_message_callback=order_callback)