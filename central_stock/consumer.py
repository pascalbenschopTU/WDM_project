import pika
import atexit
from sqlalchemy import create_engine, text
import os
from sqlalchemy.orm import sessionmaker

# connect to db
connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)

## define rabbitmq connection and channel
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
# stock requests
stock_requests = "big_db_stock_requests"
channel.queue_declare(queue=stock_requests, durable=True)

def stock_request_callback(ch, method, properties, body):
    (identifer, id) = body.decode().split(",")
    ## subtract from local stock
    with sessionmaker(bind=engine) as session:
        statement = text("SELECT stock FROM stock WHERE id=:id")
        result = session.execute(statement, {"id": id})
        for row in result:
            current_stock = row["stock"]
        withdraw_amount = 0
        if (current_stock > 100):
            withdraw_amount = 100
        elif (current_stock < 100) and current_stock > 0:
            withdraw_amount = current_stock
        if withdraw_amount > 0:
            update_statement = "UPDATE stock SET stock = stock - :amount WHERE id = :id"
            session.execute(update_statement, {"amount": withdraw_amount, "id": id})
            message = f"{id},{withdraw_amount}"
            ## put stock on queue to the requesting api
            channel.basic_publish(exchange='',
                routing_key=identifer,
                body=message)
        session.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=stock_requests, on_message_callback=stock_request_callback)

def new_item_callback(ch, method, properties, body):
    (id, price) = body.decode().split(",")
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