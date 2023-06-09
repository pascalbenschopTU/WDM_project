import os

from flask import Flask
from flask_pymongo import PyMongo, ObjectId
import pika
import requests

from Order import Order
import uuid

STOCK_URL = "http://stock-service:5000"
PAYMENT_URL = "http://payment-service:5000"

app = Flask("order-service")

hostname = os.environ['MONGODB_HOSTNAME']
hostname2 = os.environ['MONGODB_HOSTNAME_2']
database = os.environ['MONGODB_DATABASE']
gateway_url = os.environ['GATEWAY_URL']


app.config["MONGO_URI"] = f"mongodb://{hostname}:28017,{hostname2}:28118/{database}"

mongo = PyMongo(app)
db = mongo.db
orders = db.orders

# define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
channel.queue_declare(queue="stock", durable=True)
channel.queue_declare(queue="payment", durable=True)


def get_order(order_id: int) -> Order:
    order = orders.find_one({'_id': ObjectId(order_id)})

    # Check if we found an order with the given id
    if order is None or None in order:
        return None

    # Convert and return the order
    return Order.from_mongo_output(order)


def store_order(order: Order):
    orders.update_one(
        {'_id': ObjectId(order.order_id)},
        {'$set': order.to_mongo_input()}
    )


@app.post('/create/<user_id>')
def create_order(user_id):
    order = orders.insert_one(Order.create_empty(user_id))
    order_id = order.inserted_id
    return {"order_id": str(order_id)}, 200


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    result = orders.delete_one({'_id': ObjectId(order_id)})

    # Check if we deleted an order
    if result.deleted_count == 1:
        return f'Succesfully removed order with id {order_id}', 200

    return f'Could not remove order with id {order_id}', 400


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    # Find the item
    response: requests.Response = requests.get(f"{STOCK_URL}/find/{item_id}")
    if response.status_code == 404:
        return f'Could not find {item_id}', 404

    item_price = response.json()['price']

    result = orders.update_one(
        {'_id': ObjectId(order_id)},
        {
            '$set': {f'items.{item_id}': item_price},
            '$inc': {'total_price': item_price}
        },
    )

    if result.modified_count != 1:
        return {'Error': 'Order not found'}, 404

    return f'Added item {item_id} to the order', 200


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):

    # Find the order
    order = get_order(order_id)

    # Case where the other is not found
    if order is None:
        return f'Could not find an order with order_id {order_id}', 400

    # Check if the order contains the item to remove
    if not item_id in order.items:
        return f'The order with id {order_id} did not contain an item with id {item_id}', 400

    result = orders.update_one(
        {
            '_id': ObjectId(order_id)
        },
        {
            '$unset': {f'items.{item_id}'},
            '$inc': {'total_price': -order.items[item_id]}
        }
    )
    if result.modified_count != 1:
        return {'Error': 'Item not found'}, 404

    return f'Removed item {item_id} from the order', 200


@app.get('/find/<order_id>')
def find_order(order_id):

    order = get_order(order_id)

    # Check if we found an order with the given id
    if order is None:
        return f'Could not find an order with id {order_id}', 400

    # Only return item id's
    response = order.to_response()
    response['items'] = list(order.items)
    return response, 200


@app.post('/checkout/<order_id>')
def checkout(order_id):
    order = get_order(order_id)

    # Check if we found an order with the given id
    if order is None:
        return f'Could not find an order with id {order_id}', 400

    reserved_items = []

    try:
        for item in order.items:
            item_idempotency_key = uuid.uuid4()
            item_request_headers = {
                'Idempotency-Key': str(item_idempotency_key)}
            order_response = requests.post(
                f"{STOCK_URL}/subtract/{item}/1", headers=item_request_headers)
            if not (200 <= order_response.status_code < 300):
                raise Exception("Not enough stock")
            reserved_items.append(item)

        payment_idempotency_key = uuid.uuid4()
        payment_request_headers = {
            'Idempotency-Key': str(payment_idempotency_key)}
        payment_response = requests.post(
            f"{PAYMENT_URL}/pay/{order.user_id}/{order_id}/{order.total_price}", headers=payment_request_headers)

        if not (200 <= payment_response.status_code < 300):
            raise Exception("Not enough credit")
        result = orders.update_one(
            {
                '_id': ObjectId(order_id)
            },
            {
                '$set': {f'paid': True},
            }
        )

        if result.modified_count != 1:
            return {'Error': 'Order not found'}, 404
    except Exception as e:
        # Roll back the reserved items
        message = "inc,"
        for item in reserved_items:
            message += item + ","
        message = message[:-1]
        channel.basic_publish(exchange='',
                              routing_key='stock',
                              body=message)
        if hasattr(e, 'message'):
            return e.message, 400
        return str(e), 400

    return "Checkout succeeded", 200
