import os

from flask import Flask
from flask_pymongo import PyMongo, ObjectId

app = Flask('payment-service')

username = os.environ['MONGODB_USERNAME']
password = os.environ['MONGODB_PASSWORD']
hostname = os.environ['MONGODB_HOSTNAME']
database = os.environ['MONGODB_DATABASE']
gateway_url = os.environ['GATEWAY_URL']

# app.config["MONGO_URI"] = f"mongodb://{username}:{password}@{hostname}:27017/{database}"
app.config["MONGO_URI"] = f"mongodb://{hostname}:27017,{hostname}:27118/{database}"


mongo = PyMongo(app)
db = mongo.db

user_collection = db.users
paid_order_collection = db.paid_orders

@app.post('/create_user')
def create_user():
    user = user_collection.insert_one({'credit': 0}) 
    user_id = user.inserted_id
    return {'user_id': str(user_id)}



@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    user = user_collection.find_one({'_id': ObjectId(user_id)})
    if user is None:
        return {'Error': 'User not found'}, 404
    return {'user_id': user_id, 'credit': user['credit']}, 200


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    
    amount = int(amount)

    if amount < 0:
        return {'Error': 'Amount must be positive'}, 400
    
    result = user_collection.update_one(
        # Filter to check if the credit is unchanged
        {'_id': ObjectId(user_id)},
        {'$inc': {'credit': amount}}
    )

    if result.modified_count != 1:
        return {'Error': 'User not found'}, 404
    
    return {'Success': 'Credit is updated successfully'}, 200



@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    
    amount = int(amount)

    order = paid_order_collection.find_one({'order_id': order_id})

    if order:
        return 'Order already paid', 401

    user = user_collection.find_one({'_id': ObjectId(user_id)})
    if user is None:
        return {'Error': 'User not found'}, 404
    
    result = user_collection.update_one(
        # Filter to check if the credit is unchanged
        {'_id': ObjectId(user_id), 'credit': { '$gte': amount}},
        {'$inc': {'credit': -amount}}
    )

    if result.modified_count != 1:
        return {'Error': 'Not enough credit'}, 400

    paid_order_collection.insert_one({'order_id': order_id, 'amount': amount}) 
    return 'Success', 200


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    order = paid_order_collection.find_one({'order_id': order_id})
    if order is None:
        return {'Error': 'Order not found'}, 404

    amount = int(order['amount'])
    
    user = user_collection.find_one({'_id': ObjectId(user_id)})
    if user is None:
        return {'Error': 'User not found'}, 404
    
    credit = int(user['credit'])

    newCredit = credit + amount
    result = user_collection.update_one(
        # Filter to check if the credit is unchanged
        {'_id': ObjectId(user_id), 'credit': { '$eq': credit}},
        {'$set': {'credit': newCredit}}
    )

    if result.modified_count != 1:
        return {'Error': 'Something went wrong checking cancelling the order'}, 400

    paid_order_collection.delete_one({'order_id': order_id})
    return 'Success', 200


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    order = paid_order_collection.find_one({'order_id': order_id})
    return order is not None