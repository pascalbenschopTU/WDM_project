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


def get_order(order_id: int) -> Order:
    byte_result = db.hmget(f'order:{order_id}', 'user_id', 'items', 'paid')
    
    # Check if we found an order with the given id
    if None in byte_result:
        return None
    
    # Convert and return the order
    order = Order.bytes_to_order(int(order_id), byte_result)
    return order

def store_order(order: Order):
    db.hset(f'order:{order.order_id}', mapping=order.to_redis_input())

atexit.register(close_db_connection)


@app.post('/create/<user_id>')
def create_order(user_id):
    order_id = db.incr('order_id')
    order = Order(order_id, user_id)
    store_order(order)
    return {"order_id": order_id}

@app.delete('/remove/<order_id>')
def remove_order(order_id):
    success: bool = bool(db.delete(f'order:{order_id}'))
    if success:
        return f'Succesfully removed order with id {order_id}', 200

    return f'Could not remove order with id {order_id}', 200



@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    # Find the order
    order = get_order(order_id)

    if order is None:
        return f'Could not find an order with order_id {order_id}', 400
    
    items = order.items
    items[item_id] = items.get(item_id, 0) + 1

    store_order(order)
    return "Added the item to the order", 200



@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    # Find the order
    order = get_order(order_id)

    if order is None:
        return f'Could not find an order with order_id {order_id}', 400
    
    items = order.items

    if not item_id in items:
        return f'The order with id {order_id} did not contain an item with id {item_id}', 400      
    elif items[item_id] > 1:
        items[item_id] -= 1
    else:
        items.pop(item_id)

    store_order(order)
    return "Removed item from the order", 200


@app.get('/find/<order_id>')
def find_order(order_id):
    order = get_order(order_id)

    # Check if we found an order with the given id
    if order is None:
        return f'Could not find an order with id {order_id}', 400

    return order.__dict__, 200



@app.post('/checkout/<order_id>')
def checkout(order_id):
    pass
