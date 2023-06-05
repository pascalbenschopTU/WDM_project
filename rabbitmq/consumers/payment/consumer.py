import pika
import requests

PAYMENT_URL = "http://payment-service:5000"


# define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672, heartbeat=600, blocked_connection_timeout=300))
channel = connection.channel()
## Forwards to stock.
channel.queue_declare(queue="payment", durable=True)
## recieves messages from stock if not in order
def add_credit(user_id: str, amount: int):
    requests.post(f"{PAYMENT_URL}/add_funds/{user_id}/{amount}")

def callback(ch, method, properties, body):
    params = body.decode().split(",")
    print("payment callback: " + body.decode())
    if params[0] == "add":
        add_credit(params[1], params[2])
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue="payment", on_message_callback=callback)
channel.start_consuming()