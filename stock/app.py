import os
import atexit
from typing import List
from flask import Flask
from sqlalchemy import create_engine

app = Flask("stock-service")

import psycopg2

# db = psycopg2.connect(
#    database=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'], host=os.environ['POSTGRES_HOST'], port=os.environ['POSTGRES_PORT']
# )
connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)

def close_db_connection():
    engine.close()

atexit.register(close_db_connection)


@app.post('/item/create/<price>')
def create_item(price: int):
    price = int(price)
    if price < 0:
        return 'Price must be positive', 400
    
    insert_item = "INSERT INTO stock (price, stock) VALUES (%s, %s) RETURNING id;"
    with engine.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(insert_item, (price, 0))
        item_id: int = cursor.fetchone()[0]
    item: dict[str, int] = {'item_id': item_id, 'price': price, 'stock': 0}
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

    get_stock = "SELECT stock FROM stock WHERE id = %s;"
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

def decrement_stock_bulk(item_ids: List[str]):
    with engine.connect() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN;")
            # Check if all stock counts are above 0.
            cursor.execute("""
                    SELECT COUNT(*)
                    FROM your_table_name
                    WHERE id = ANY(%s) AND stock <= 0
                    FOR UPDATE;
                """, (item_ids,))
            # returns ones that are not above 0
            count = cursor.fetchone()[0]
            if count > 0:
                return "Not enough stock", 404
            # If all amounts are above 0, decrement them by 1
            cursor.execute("""
                UPDATE your_table_name
                SET stock = stock - 1
                WHERE id = ANY(%s) AND stock > 0;
            """, (item_ids,))
            cursor.commit()
        except psycopg2.Error as e:
            # Handle any errors that occur during the transaction
            conn.rollback()
    return "Success", 200

