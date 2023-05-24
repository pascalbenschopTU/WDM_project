import os
import atexit
from typing import List
from flask import Flask
from sqlalchemy import create_engine
import pika
app = Flask("stock-service")
api_identifier = "xyzasd"
import uuid
import psycopg2

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
big_db = "stock_big_db"
channel.queue_declare(queue=big_db, durable=True)
channel.queue_declare(queue=api_identifier, durable=True)
channel.exchange_declare(exchange='new_items', exchange_type='fanout')


connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)

def close_db_connection():
    engine.close()

atexit.register(close_db_connection)

@app.post('/item/create/<price>')
def create_item(price: int):
    price = int(price)
    id = uuid.uuid4()
    message = f"{id},{price}"
    channel.basic_publish(exchange='logs', routing_key='', body=message)
    item: dict[str, int] = {'item_id': id, 'price': price, 'stock': 0}
    return item, 201


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item_id = int(item_id)
    get_item = "SELECT * FROM stock WHERE id = %s;"
    with engine.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(get_item, (item_id,))
        item = cursor.fetchone()
        if None in item:
            return None, 404
        item = {'item_id': int(item[0]), 'price': int(item[1]), 'stock': int(item[2])}
        return item, 200


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    return update_stock(item_id, amount)


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    return update_stock(int(item_id), amount, subtract=True)

def update_stock(item_id: str, amount: int, subtract: bool = False):
    amount = int(amount)
    if amount < 0:
        return 'Amount must be positive', 400

    get_stock = "SELECT stock FROxM stock WHERE id = %s;"
    with engine.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(get_stock, (item_id,))
        stock = int(cursor.fetchone()[0])
        new_stock = stock - amount if subtract else stock + amount
        if new_stock < 0:
            return 'Not enough stock', 400
        update_stock = "UPDATE stock SET stock = %s WHERE id = %s;"
        cursor.execute(update_stock, (new_stock, item_id))
        return "Success", 200

@app.post('/subtract_bulk/<item_ids>')
def decrement_stock_bulk(item_ids: str):
    ids = item_ids.split(",")
    with engine.connect() as conn:
        cursor = conn.cursor()
        try:
            # Check if all stock counts are above 0.
            items = cursor.execute("""
                    SELECT (id, stock)
                    FROM stock
                    WHERE id = ANY(%s) AND stock > 0
                    FOR UPDATE;
                """, (ids,))
            # if it's above 0, it isn't possible for all of them
            for (id, amount) in items:
                if amount <= 0:
                    ## post message that we need more stock
                    channel.basic_publish(exchange='',
                        routing_key=big_db,
                      body=f"{api_identifier},{id}")
                    ## release transaction
                    cursor.execute("END;")
                    cursor.commit()
                    return f"Not enough of {id}", 400
            # If all amounts are above 0, decrement them by 1
            cursor.execute("""
                UPDATE stock
                SET stock = stock - 1
                WHERE id = ANY(%s) AND stock > 0;
            """, (ids,))
            cursor.execute("END;")
            cursor.commit()
        except psycopg2.Error as e:
            # Handle any errors that occur during the transaction
            conn.rollback()
            return "Something went wrong", 400
    return f"{api_identifier}", 200