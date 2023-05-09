import os
import atexit

from flask import Flask
import redis
import pika

gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create/<user_id>')
def create_order(user_id):
    pass


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    pass


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    pass


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    pass


@app.get('/find/<order_id>')
def find_order(order_id):
    return 200
    pass


@app.post('/checkout/<order_id>')
def checkout(order_id):
    return 200
    #return initiate_order(order_id)

## define channels
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672))
channel = connection.channel()
## Forwards to stock.
channel.queue_declare(queue=os.environ['order_stock'], durable=True)
## Recieves ok from payment if withdrawl was ok
channel.queue_declare(queue=os.environ['payment_order'], durable=True)
## recieves messages from stock if not in order
channel.queue_declare(queue=os.environ['stock_order'], durable=True)

def generate_stock_message(action, order):
    message = f"{order.order_id},{order.user_id},{action},"
    for item in order.items.values():
        message += item.item_id
    return message

# [0] = orderId, [1] = successfull, [3] = serivce
def order_status_callback(response):
    def callback(ch, method, properties, body):
        params = body.decode().split(",")
        order = find_order(params[0])
        ## this only comes from the payment service
        if params[1] == "True":
            order.paid = True
            ## TODO persist in db.
        else:
            ## if payment didn't go through, we reverse the changes made to the stock.
            if params[2] == "payment":
                message = generate_stock_message("dec", order)
                channel.basic_publish(
                    exchange='',
                    routing_key=os.environ['order_stock'],
                    body=message,
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ))
        ## Delete queue as we will not use it anymore
        channel.queue_delete(queue=params[0])
        response[0] = params[1] == "True"
        ch.basic_ack(delivery_tag=method.delivery_tag)
    return callback


def initiate_order(order_id):
    #order = find_order(order_id)
    #order = {"order_id": order_id, "user_id": 1, "items": [{"item_id": 1}, {"item_id": 2}]}
    print("orderxxxx")
    print("restart")
    #message = generate_stock_message("dec", order)
    message = "1,1,dec,1"
    callback_queue = channel.queue_declare(queue=order_id, durable=True)
    print("initate order message: " + message)
    channel.basic_publish(
        exchange='',
        routing_key=os.environ['order_stock'],
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
            reply_to=order_id
    ))
    ## this looks stupid but i need something that passes by reference, and i don't know enough about this to figure out something else.
    order_ok = [False]
    callback = order_status_callback(order_ok)
    channel.basic_consume(queue=order_id, on_message_callback=callback)
    print("before stopxxx")
    ## TODO is this in ms?
    ## block thread until either response from payment service or stock service on the order_id channel
    channel.connection.process_data_events(time_limit=5)
    if order_ok[0]:
        return "Success", 200
    else:
        return "Stock or payment failed", 400

channel.start_consuming()