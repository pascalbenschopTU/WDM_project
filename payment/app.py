import os
import atexit
from flask import Flask
import redis

app = Flask('payment-service')
gateway_url = os.environ['GATEWAY_URL']

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create_user')
def create_user():
    user_id = db.incr('user_id')
    user = {'user_id': user_id, 'credit': 0}
    db.hmset(f'user:{user_id}', user)
    return user, 200


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    user = db.exists(f'user:{user_id}')
    if not user:
        return {'Error': 'User not found'}, 404
    return user, 200


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    if int(amount) < 0:
        return {'Error': 'Amount must be positive'}, 400
    if not db.exists(f'user:{user_id}'):
        return {'Error': 'User not found'}, 400
    db.hincrby(f'user:{user_id}', 'credit', int(amount))
    return 'Success', 200


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    credit = db.hget(f'user:{user_id}', 'credit')
    if int(credit) < int(amount):
        return {'Error:', 'Not enough credit'}, 400
    order = db.exists(f'paid_orders:{order_id}')

    if order:
        return 'Order already paid', 400

    p = db.pipeline(transaction=True)
    p.hincrby(f'user:{user_id}', 'credit', -int(amount))
    p.hmset(f'paid_orders:{order_id}', {
            'amount_paid': amount, 'user_id': user_id})
    p.execute()
    return 'Success', 200


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    order = db.hgetall(f'paid_orders:{order_id}')
    if not order:
        return {'Error': 'Order not found'}, 404

    amount = order['amount_paid']
    p = db.pipeline(transaction=True)
    p.hincrby(f'user:{user_id}', 'credit', amount)
    p.delete(f'paid_orders:{order_id}')
    p.execute()
    return 'Success', 200


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    user = db.exists(f'user:{user_id}')
    if not user:
        return {'Error': 'User not found'}, 404

    paid_order = db.exists(f'paid_orders:{order_id}')
    return {'paid': paid_order > 0}, 200

## define channels
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672))
channel = connection.channel()
## Forwards to stock.
channel.queue_declare(queue="payment", durable=True)
## recieves messages from stock if not in order

def callback(ch, method, properties, body):
    params = body.decode().split(",")
    print("payment callback: " + body.decode())
    if params[0] == "add":
        add_credit(params[1], params[2])
    if params[0] == "remove":
        remove_credit(params[1], params[2])
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue="payment", on_message_callback=callback)
channel.start_consuming()
