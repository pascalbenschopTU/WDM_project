import pika
import atexit
from sqlalchemy import create_engine
import os

# connect to db
connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)
atexit.register(engine.close())

## define rabbitmq connection and channel
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
# stock requests
stock_requests = "big_db_stock_requests"
channel.queue_declare(queue=stock_requests, durable=True)

def stock_request_callback(ch, method, properties, body):
    (identifer, id) = body.decode().split(",")
    ## subtract from local stock
    with engine.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT stock FROM stock WHERE id={id}")
        current_stock = cursor.fetchone()
        withdraw_amount = 0
        if (current_stock > 100):
            withdraw_amount = 100
        elif (current_stock < 100) and current_stock > 0:
            withdraw_amount = current_stock
        if withdraw_amount > 0:
            cursor.execute("""
                UPDATE stock
                SET stock = stock - %s
                WHERE id = %s;
            """, (withdraw_amount, id,))
            message = f"{id},{withdraw_amount}"
            ## put stock on queue to the requesting api
            channel.basic_publish(exchange='',
                routing_key=identifer,
                body=message)
    cursor.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=stock_requests, on_message_callback=stock_request_callback)
channel.start_consuming()

# new items queue
new_items = "new_items"
channel.exchange_declare(exchange=new_items, exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange=new_items, queue=queue_name)

def new_item_callback(ch, method, properties, body):
    (id, price) = body.decode().split(",")
    with engine.connect() as conn:
        insert_item = "INSERT INTO stock (id, price, stock) VALUES (%s, %s, %s) RETURNING id;"
        cursor = conn.cursor()
        cursor.execute(insert_item, (id, price, 0))
        ch.basic_ack(delivery_tag=method.delivery_tag)
## todo can i consume multiple queues?
channel.basic_consume(
    queue=queue_name, on_message_callback=new_item_callback, auto_ack=True)

channel.start_consuming()