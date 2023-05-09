import os
import atexit

from flask import Flask
import redis
import pika

app = Flask("payment-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create_user')
def create_user():
    pass


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    pass


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    pass


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    pass


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    pass


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    pass

## define channels
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672))
channel = connection.channel()
## Forwards to stock.
channel.queue_declare(queue=os.environ['payment_order'], durable=True)
## Recieves ok from payment if withdrawl was ok
channel.queue_declare(queue=os.environ['stock_payment'], durable=True)
## recieves messages from stock if not in order

def stock_callback(ch, method, properties, body):
    params = body.decode()
    print("stock_callback: " + body.decode())
    status = remove_credit(params[1], params[0], params[2])
    message = f"{params[0]},True,payment"
    if status > 399: ## if something went wrong, we change the message
        message = f"{params[0]},False,payment"
    # we publish it to the queue the order service is listening on.
    channel.basic_publish(
        exchange='',
        routing_key=params[0],
        body=message,
        properties=pika.BasicProperties(
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
    ))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=os.environ['stock_payment'], on_message_callback=stock_callback)
channel.start_consuming()