import pika
import psycopg2
import atexit
import os
api_identifier = "xyzasd"
STOCK_URL = "http://stock-service:5000"

## define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
channel.queue_declare(queue=api_identifier, durable=True)
# connect to db

db = psycopg2.connect(
    database=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'], host=os.environ['POSTGRES_HOST'], port=os.environ['POSTGRES_PORT']
)
atexit.register(db.close())


## update stock
def update_stock_callback(ch, method, properties, body):
    (id, amount) = body.decode().split(",")
    with open('/HOME/FLASK-APP/log.txt', 'a') as f:
    # Write some data to the file
        f.write(body.decode() + "\n")
    cursor = db.cursor()
    statement = f"UPDATE stock SET stock = stock + {amount} WHERE id = {id}"
    cursor.execute(statement)
    cursor.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=api_identifier, callback=update_stock_callback)
channel.start_consuming()

# new items queue
new_items = "new_items"
channel.exchange_declare(exchange=new_items, exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange=new_items, queue=queue_name)

def new_item_callback(ch, method, properties, body):
    (id, price) = body.decode().split(",")
    insert_item = "INSERT INTO stock (id, price, stock) VALUES (%s, %s, %s) RETURNING id;"
    cursor = db.cursor()
    cursor.execute(insert_item, (id, price, 0))
    ch.basic_ack(delivery_tag=method.delivery_tag)
## todo can i consume multiple queues?
channel.basic_consume(
    queue=queue_name, on_message_callback=new_item_callback, auto_ack=True)

channel.start_consuming()