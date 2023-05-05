import os
import atexit

from flask import Flask
import redis

from Order import Order

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
    order_id = db.incr('order_id')
    order = Order(order_id, user_id)
    db.hset(f'order:{order_id}', mapping=order.to_redis_input())
    return {"order_id": order_id}

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
    byte_result = db.hmget(f'order:{order_id}', 'user_id', 'items', 'paid')
    
    # Check if we found an order with the given id
    if None in byte_result:
        return f'Could not find an order with id {order_id}', 400
    
    # Convert and return the order
    order = Order.bytes_to_order(int(order_id), byte_result)
    return order.__dict__, 200


@app.post('/checkout/<order_id>')
def checkout(order_id):
    pass
