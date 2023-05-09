import os
import atexit

from flask import Flask
import redis
import requests

from Order import Order

STOCK_URL = "http://stock-service:5000"
PAYMENT_URL = "http://payment-service:5000"
gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()

atexit.register(close_db_connection)

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

    # Case where the other is not found
    if order is None:
        return f'Could not find an order with order_id {order_id}', 400
    
    items: list[str] = order.items
    items.append(item_id)
    store_order(order)
    return f'Added item {item_id} to the order', 200



@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    # Find the order
    order = get_order(order_id)

    # Case where the other is not found
    if order is None:
        return f'Could not find an order with order_id {order_id}', 400
    
    items: list[str] = order.items

    # Check if the order contains the item to remove
    if not item_id in items:
        return f'The order with id {order_id} did not contain an item with id {item_id}', 400      
    else:
        items.remove(item_id)

    store_order(order)
    return f'Removed item {item_id} from the order', 200


@app.get('/find/<order_id>')
def find_order(order_id):

    order = get_order(order_id)

    # Check if we found an order with the given id
    if order is None:
        return f'Could not find an order with id {order_id}', 400

    return order.__dict__, 200



@app.post('/checkout/<order_id>')
def checkout(order_id):
    order = get_order(order_id)

    # Check if we found an order with the given id
    if order is None:
        return f'Could not find an order with id {order_id}', 400
    
    totalOrderPrice = 0
    print(gateway_url)
    for item in order.items:
        response: requests.Response = requests.get(f"{STOCK_URL}/find/{item}")
        totalOrderPrice += response.json()['price']
    
    
    reserved_items = []

    try:
        for item in order.items:
            order_response = requests.post(f"{STOCK_URL}/subtract/{item}/1")
            if not (200 <= order_response.status_code < 300):
                raise Exception("Not enough stock") 
            reserved_items.append(item)


        payment_response = requests.post(f"{PAYMENT_URL}/pay/{order.user_id}/{order_id}/{totalOrderPrice}")

        if not (200 <= payment_response.status_code < 300):
            raise Exception("Not enough credit") 
        order.paid = True
        store_order(order)
    except:
        # Roll back the reserved items
        for item in reserved_items:
            requests.post(f"{STOCK_URL}/add/{item}/1")
        return "Checkout failed", 400
    
    return "Checkout succeeded", 200

