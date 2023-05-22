import os
import atexit

from flask import Flask

app = Flask("stock-service")

import psycopg2

conn = psycopg2.connect(
   database=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'], host=os.environ['POSTGRES_HOST'], port=os.environ['POSTGRES_PORT']
)
    
cursor = conn.cursor()

def close_db_connection():
    conn.close()

atexit.register(close_db_connection)


@app.post('/item/create/<price>')
def create_item(price: int):
    price = int(price)
    if price < 0:
        return 'Price must be positive', 400
    
    insert_item = "INSERT INTO stock (price, stock) VALUES (%s, %s) RETURNING id;"
    cursor.execute(insert_item, (price, 0))
    item_id: int = cursor.fetchone()[0]
    item: dict[str, int] = {'item_id': item_id, 'price': price, 'stock': 0}
    return item, 201


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item_id = int(item_id)
    get_item = "SELECT * FROM stock WHERE id = %s;"
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
    item_id = int(item_id)
    amount = int(amount)
    if amount < 0:
        return 'Amount must be positive', 400
    
    get_stock = "SELECT stock FROM stock WHERE id = %s;"
    cursor.execute(get_stock, (item_id,))
    stock = int(cursor.fetchone()[0])
    new_stock = stock - amount if subtract else stock + amount
    if new_stock < 0:
        return 'Not enough stock', 400
    update_stock = "UPDATE stock SET stock = %s WHERE id = %s;"
    cursor.execute(update_stock, (new_stock, item_id))
    return "Success", 200
    



