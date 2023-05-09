import os
import atexit

from flask import Flask
import redis


app = Flask("stock-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/item/create/<price>')
def create_item(price: int):
    item_id = db.incr('item_id')
    item = {'item_id': item_id, 'price': price, 'stock': 0}
    db.hset(f'item:{item_id}', mapping=item)

    return item, 201


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item = db.hmget(f'item:{item_id}', 'price', 'stock')
    if None in item:
        return None, 404

    return {'item_id': item_id, 'price': int(item[0]), 'stock': int(item[1])}, 200


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    db.hincrby(f'item:{item_id}', 'stock', int(amount))
    return "Success", 200


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    stock = db.hget(f'item:{item_id}', 'stock')
    if int(stock) < int(amount):
        return "Not enough stock", 400
    else:
        db.hincrby(f'item:{item_id}', 'stock', -int(amount))
        return "Success", 200

@app.post('/subtract_bulk/<item_ids>')
def remove_stock_bulk(item_ids: list[str]):
    for i in range(0, len(item_ids)):
        response = remove_stock(item_ids[0])
        if (response > 299):
            for j in range(0, i):
                add_stock(item_ids[j])
            return 400
    return 200

@app.post('/add_bulk/<item_ids>')
def remove_stock_bulk(item_ids: list[str]):
    [add_stock(item_id) for item_id in item_ids]
    return 200
