import os
import sys
from flask import Flask
import redis
from flask_pymongo import PyMongo, ObjectId

app = Flask('payment-service')

username = os.environ['MONGODB_USERNAME']
password = os.environ['MONGODB_PASSWORD']
hostname = os.environ['MONGODB_HOSTNAME']
database = os.environ['MONGODB_DATABASE']
gateway_url = os.environ['GATEWAY_URL']

app.config["MONGO_URI"] = 'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27018/' + os.environ['MONGODB_DATABASE']
mongo = PyMongo(app)
db = mongo.db



@app.post('/create_user')
def create_user():
    print("did this", file=sys.stderr)
    collection = db.users
    user = collection.insert_one({'credit': 0})
    return {'user_id': 0}
    user_id = user.inserted_id
    return {'user_id': user_id}



@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    user = db.hmget(f'user:{user_id}', 'credit')
    if None in user:
        return {'Error': 'User not found'}, 404
    return {"user_id": int(user_id), "credit": int(user[0])}, 200


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
        return 'Not enough credit', 400
    order = db.exists(f'paid_orders:{order_id}')

    if order:
        return 'Order already paid', 401

    p = db.pipeline(transaction=True)
    p.hincrby(f'user:{user_id}', 'credit', -int(amount))
    p.hmset(f'paid_orders:{order_id}', {
            'amount_paid': amount, 'user_id': user_id})
    p.execute()
    return 'Success', 200


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    order = db.hmget(f'paid_orders:{order_id}', 'amount_paid')
    if None in order:
        return {'Error': 'Order not found'}, 404

    amount = order[0]
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
