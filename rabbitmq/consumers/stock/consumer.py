import pika
import requests
import uuid

STOCK_URL = "http://stock-service:5000"

# define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
channel.queue_declare(queue="stock", durable=True)


def add_stock(item_id: str, amount: int):
    idempotency_key = str(uuid.uuid4())
    headers = {"Idempotency-Key": idempotency_key}
    requests.post(f"{STOCK_URL}/add/{item_id}/{amount}", headers=headers)


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
