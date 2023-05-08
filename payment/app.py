import os
import atexit

from flask import Flask
import redis
import requests


app = Flask("payment-service")
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
    db.hset(f'user:{user_id}', mapping=user)
    return user, 200


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    user = db.hmget(f'item:{user_id}', 'credit')
    if None in user:
        return {"Error": "User not found"}, 404

    return {'user_id': user_id, 'credit': int(user[0])}, 200


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    db.hincrby(f'item:{user_id}', 'credit', int(amount))
    return {'done': True}, 200


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    credit = db.hget(f'item:{user_id}', 'credit')
    if int(credit) < int(amount):
        return {"Error:", "Not enough credit"}, 400
    p = db.pipeline(transaction=True)
    p.hincrby(f'user:{user_id}', 'credit', -int(amount))
    p.hset(f'order:{order_id}', 'status', 'paid')
    p.execute()
    return "Success", 200


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    user = db.hget(f'user:{user_id}', 'paid_orders')
    if user:
        response = requests.get(f"{gateway_url}/orders/find/{order_id}")
        if response.status_code != 200:
            return {"Error": "Order not found"}, 404
        order = response.json()
        requests.delete(f"{gateway_url}/orders/remove/{order_id}")
        amount = order["total_cost"]

        db.hincrby(f'user:{user_id}', 'credit', amount)
        db.hdel(f'user:{user_id}', 'paid_orders')
        for item_id in order["items"]:
            requests.post(f"{gateway_url}/stock/add/{item_id}/1")

        return {"Success": True}, 200
    else:
        return {"Error": "Payment not found"}, 404


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    user = db.hget(f'user:{user_id}', 'paid_orders')
    if user:
        order = requests.get(f"{gateway_url}/orders/find/{order_id}").json()
        return {'paid': order['paid']}, 200
    return {'Error': 'User not found'}, 404
