import psycopg2
import os
import atexit

from flask import Flask, request

app = Flask("stock-service")


db = psycopg2.connect(
    database=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ[
        'POSTGRES_PASSWORD'], host=os.environ['POSTGRES_HOST'], port=os.environ['POSTGRES_PORT']
)

db.autocommit = True

cursor = db.cursor()


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


def check_idempotency_key(idempotency_key: str) -> dict | None:
    if idempotency_key is None:
        return None
    find_idempotency_key = "SELECT * FROM idempotency_keys WHERE idempotency_key = %s;"
    if cursor.execute(find_idempotency_key, (idempotency_key,)):
        return {'Success': 'Request already fulfilled'}, 200
    cursor.execute(
        "INSERT INTO idempotency_keys (idempotency_key) VALUES (%s);", (idempotency_key,))
    return None


@app.post('/item/create/<price>')
def create_item(price: int):
    check_idempotency_key_result = check_idempotency_key(
        request.headers.get('Idempotency-Key'))
    if check_idempotency_key_result is not None:
        return check_idempotency_key_result
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
    if item is None:
        return {'Error': 'Item not found'}, 404
    item = {'item_id': int(item[0]), 'price': int(
        item[1]), 'stock': int(item[2])}
    return item, 200


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    check_idempotency_key_result = check_idempotency_key(
        request.headers.get('Idempotency-Key'))
    if check_idempotency_key_result is not None:
        return check_idempotency_key_result
    return update_stock(item_id, amount)


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    check_idempotency_key_result = check_idempotency_key(
        request.headers.get('Idempotency-Key'))
    if check_idempotency_key_result is not None:
        return check_idempotency_key_result
    return update_stock(int(item_id), amount, subtract=True)


def update_stock(item_id: str, amount: int, subtract: bool = False):
    item_id = int(item_id)
    amount = int(amount)
    if amount < 0:
        return 'Amount must be positive', 400

    if subtract:
        update_stock = "UPDATE stock SET stock = stock - %s WHERE id = %s AND stock >= %s;"
        cursor.execute(update_stock, (amount, item_id, amount))
        if (cursor.rowcount != 1):
            return 'Not enough stock', 400

    else:
        update_stock = "UPDATE stock SET stock = stock + %s WHERE id = %s;"
        cursor.execute(update_stock, (amount, item_id))
    return "Success", 200
