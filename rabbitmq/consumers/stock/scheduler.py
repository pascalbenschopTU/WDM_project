import pika
from sqlalchemy import create_engine, text
import os
import time
import threading
from stock_item import StockTransaction, Statement, SelectStatement
import asyncio
import sys
import builtins
import logging
queue_identifier = os.environ["QUEUE_IDENTIFIER"]
STOCK_URL = "http://stock-service:5000"
big_db = "big_db_stock_requests"
## define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)
subtract_transactions: list[(int,StockTransaction)] = []
add_requests: list[(int,Statement)] = []
ids: list[(int,str)] = []
select_statements: list[(int,SelectStatement)] = []

interval = 10
window_start = 0
timestamp_of_last_message = 0
since_last_execution = 0
## everytime all current transactions have been read, we can read from here.
##

def send_response(reply_to, correlation_id, message):
    global channel
    channel.basic_publish(exchange='',
                     routing_key=reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         correlation_id),
                     body=message)

def stringify_stock_transaction(transaction):
    return_string = ""
    for statement in transaction.statements:
        return_string += "{" + f"item_id: {statement.item_id}, amount: {statement.amount}" + "},"
    return return_string

def convert_to_transaction(queue_identifier: str, correlation_id: str, csv_items: list[str]) -> StockTransaction:
    statements = []
    for i in range(0, len(csv_items), 2):
        (id, amount) = (csv_items[i], csv_items[i+1])
        statements.append(Statement(id, int(amount)))
    return StockTransaction(queue_identifier, correlation_id, statements)

def get_transaction_item_ids(queue_message: list[str]) -> list[str]:
    ids = []
    for i in range(0, len(queue_message), 2):
        id = queue_message[i]
        ids.append(id)
    return ids

def get_items(ids: list[str], db_connection) -> dict[int]:

    select_statement = text("SELECT * FROM stock WHERE id=ANY(:ids)")
    unique_ids = list(set(ids))
    items: dict[int] = {}
    # with engine.connect().execution_options(isolation_level="READ UNCOMMITTED") as db_connection:
    rows = db_connection.execute(select_statement, {"ids": unique_ids})
    for row in rows:
        items[row[0]] = int(row[2])
    # db_connection.commit()
    return items

def persist_transactions(items: dict[int], db_connection):
    with engine.connect() as db_connection:
        for id in items.keys():
            update_statement = text("UPDATE stock SET stock = :stock WHERE id=:id;")
            db_connection.execute(update_statement, {"id": id, "stock": items[id]})
    
def execute_transactions(subtract_transactions: list[StockTransaction], items: dict[int], add_statements: list[Statement]):
    ## first we add to our stock
    for add in add_statements:
        items[add.item_id] += add.amount
    ## All of those are good enough, we can always add
    for subtract_transaction in subtract_transactions:
        items_clone = items
        all_successfull = True
        for statement in subtract_transaction.statements:
            if items[statement.item_id] >= statement.amount:
                items_clone[statement.item_id] = items[statement.item_id] - statement.amount
            else:
                send_response(subtract_transaction.transaction_id, subtract_transaction.correlation_id, f"Not enough stock of {statement.item_id}")
                all_successfull = False
                break
        if all_successfull:
            items = items_clone
            send_response(subtract_transaction.transaction_id, subtract_transaction.correlation_id, "Success")
    return items
    
def get_index(items, max_time):
    return 1
    # for i in range(0, len(items)):
    #     ## if id is larger than window, then we know what to remove
    #     if items[i][0] > max_time:
    #         return items[i][1]
    
def execute_window(current_window: int):
    global ids
    id_index = get_index(ids, current_window + interval)
    current_ids = [id[1] for id in ids[:id_index]]
    ids = ids[id_index:]
        
    global subtract_transactions
    subtract_index = get_index(subtract_transactions, current_window + interval)
    current_subtract_transactions = [t[1] for t in subtract_transactions[:subtract_index]]
    subtract_transactions = subtract_transactions[subtract_index:] 
    
    global add_requests
    add_index = get_index(add_requests, current_window + interval)
    current_add_requests = [t[1] for t in add_requests[:add_index]]
    add_requests = add_requests[add_index:]
    with engine.connect() as db_connection:
        items = get_items(current_ids, db_connection)
        execute_transactions(current_subtract_transactions, items, current_add_requests)
        persist_transactions(items, db_connection)
        db_connection.commit()
        

def set_timestamps(timestamp: int):
    global timestamp_of_last_message
    timestamp_of_last_message = timestamp
    global since_last_execution
    since_last_execution = 0
    global window_start
    if window_start + interval < timestamp:
        current_window = window_start
        window_start = timestamp
        execute_window(current_window)
        # thread_1 = threading.Thread(target=execute_window, args=current_window)
        # thread_1.start()
        
def subtract_transaction_callback(ch, method, properties, body):
    params = body.decode().split(",") #first is timestamp, and then id, amount multiple times for each item they want to decrement.
    timestamp = int(params[0])
    transaction = convert_to_transaction(properties.reply_to, properties.correlation_id, params[1:])
    subtract_transactions.append((timestamp, transaction))
    transaction_ids = get_transaction_item_ids(params[1:])
    # send_response(properties.reply_to, properties.correlation_id, properties.timestamp)
    [ids.append((timestamp, id)) for id in transaction_ids]
    set_timestamps(timestamp)
    
subtract = "subtract"
channel.exchange_declare(exchange=subtract, exchange_type='fanout', durable=True)
result = channel.queue_declare(queue='', durable=True)
queue_name = result.method.queue
channel.queue_bind(exchange=subtract, queue=queue_name)
channel.basic_consume(queue=queue_name, on_message_callback=subtract_transaction_callback, auto_ack=True)

def find_item(ch, method, properties, body):
    params = body.decode().split(",") #first is timestamp, and then id, amount multiple times for each item they want to decrement.
    timestamp = int(params[0])
    transaction = convert_to_transaction(properties.reply_to, properties.correlation_id, params[1:])
    subtract_transactions.append((timestamp, transaction))
    transaction_ids = get_transaction_item_ids(params[1:])
    # send_response(properties.reply_to, properties.correlation_id, properties.timestamp)
    [ids.append((timestamp, id)) for id in transaction_ids]
    set_timestamps(timestamp)
    
subtract = "subtract"
channel.exchange_declare(exchange=subtract, exchange_type='fanout', durable=True)
result = channel.queue_declare(queue='', durable=True)
queue_name = result.method.queue
channel.queue_bind(exchange=subtract, queue=queue_name)
channel.basic_consume(queue=queue_name, on_message_callback=subtract_transaction_callback, auto_ack=True)
    
def add_stock_callback(ch, method, properties, body):
    (timestamp, item_id, amount) = body.decode().split(",")
    timestamp = int(timestamp)
    add_requests.append((timestamp, Statement(item_id, int(amount))))
    ids.append((timestamp, item_id))
    set_timestamps(timestamp)

add = "add"
channel.exchange_declare(exchange=add, exchange_type='fanout', durable=True)
result = channel.queue_declare(queue='', durable=True)
queue_name = result.method.queue
channel.queue_bind(exchange=add, queue=queue_name)
channel.basic_consume(queue=queue_name, on_message_callback=add_stock_callback, auto_ack=True)

# new items queue
def new_item_callback(ch, method, properties, body):
    (id, price) = body.decode().split(",")
    with engine.connect().execution_options(isolation_level="READ UNCOMMITTED") as db_connection:
        statement = text("INSERT INTO stock (id, price, stock) VALUES (:id, :price, 0);")
        db_connection.execute(statement, {"price": price, "id": id})
        db_connection.commit()
        ch.basic_ack(delivery_tag = method.delivery_tag)
   
new_items = "new_items"
channel.exchange_declare(exchange=new_items, exchange_type='fanout', durable=True)
result = channel.queue_declare(queue='', durable=True)
queue_name = result.method.queue
channel.queue_bind(exchange=new_items, queue=queue_name)
channel.basic_consume(queue=queue_name, on_message_callback=new_item_callback)

channel.start_consuming()

async def has_too_much_time_passed():
    while True:
        # 50ms
        await asyncio.sleep(0.025) 
        # Increment the counter by 50ms
        global since_last_execution
        since_last_execution += 25
        # if 100ms has passed since last time, we execute
        if since_last_execution > 25:
            execute_window(window_start+since_last_execution)
            # thread_1 = threading.Thread(target=execute_window, args=window_start+since_last_execution)
            # thread_1.start()
            
asyncio.create_task(has_too_much_time_passed())