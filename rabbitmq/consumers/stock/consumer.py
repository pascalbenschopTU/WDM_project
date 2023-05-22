import pika
import psycopg2
import os

conn = psycopg2.connect(
   database="postgres", user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'], host=os.environ['POSTGRES_HOST'], port=os.environ['POSTGRES_PORT']
)

cursor = conn.cursor()


## define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672))
channel = connection.channel()
channel.queue_declare(queue="stock", durable=True)

def add_stock(item_id: str, amount: int):
    item_id = int(item_id)
    get_stock = "SELECT stock FROM stock WHERE id = %s;"
    cursor.execute(get_stock, (item_id,))
    stock = cursor.fetchone()[0]
    stock += amount
    update_stock = "UPDATE stock SET stock = %s WHERE id = %s;"
    cursor.execute(update_stock, (stock, item_id))
    conn.commit()

def callback(ch, method, properties, body):
    params = body.decode().split(",")
    with open('/HOME/FLASK-APP/log.txt', 'a') as f:
    # Write some data to the file
        f.write(body.decode() + "\n")
    if params[0] == "inc":
        for i in range(1, len(params)):
            add_stock(params[i], 1)

    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue="stock", on_message_callback=callback)
channel.start_consuming()