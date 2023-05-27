import pika
from sqlalchemy import create_engine, text
import os
api_identifier = "xyzasd"
STOCK_URL = "http://stock-service:5000"

## define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
channel.queue_declare(queue=api_identifier, durable=True)
# connect to db

connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)

## update stock
def update_stock_callback(ch, method, properties, body):
    (id, amount) = body.decode().split(",")
    with open('/HOME/FLASK-APP/log.txt', 'a') as f:
    # Write some data to the file
        f.write(body.decode() + "\n")
    with engine.connect() as db_connection:
        statement = text("UPDATE stock SET stock = stock + :amount WHERE id = :id")
        db_connection.execute(statement, {"amount": amount, "id": id})
        db_connection.commit()
        ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=api_identifier, on_message_callback=update_stock_callback)

# new items queue


def new_item_callback(ch, method, properties, body):
    (id, price) = body.decode().split(",")
    with open('/HOME/FLASK-APP/log.txt', 'a') as f:
        f.write("new_item " + id + "," + price + "\n")
    with engine.connect() as db_connection:
        statement = text("INSERT INTO stock (id, price, stock) VALUES (:id, :price, 0);")
        db_connection.execute(statement, {"price": price, "id": id})
        db_connection.commit()
        
## todo can i consume multiple queues?
new_items = "new_items"
channel.exchange_declare(exchange=new_items, exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange=new_items, queue=queue_name)
channel.basic_consume(
    queue=queue_name, on_message_callback=new_item_callback, auto_ack=True)

channel.start_consuming()