import pika
from sqlalchemy import create_engine, text
import os
STOCK_URL = "http://stock-service:5000"
big_db = "big_db_stock_requests"
## define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
# connect to db

connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)

# new items queue
def new_item_callback(ch, method, properties, body):
    (id, price) = body.decode().split(",")
    with open('/home/stock-app/log.txt', 'a') as f:
        f.write("new_item " + id + "," + price + "\n")
    with engine.connect() as db_connection:
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