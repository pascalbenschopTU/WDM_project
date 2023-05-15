import redis
import pika
import os

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))

# define channels
connection = pika.BlockingConnection( #rabbitmq
    pika.ConnectionParameters(host='rabbitmq', port=5672))
channel = connection.channel()
## Forwards to stock.
channel.queue_declare(queue="payment", durable=True)
## recieves messages from stock if not in order
def add_credit(user_id: str, amount: int):
    db.hincrby(f'user:{user_id}', 'credit', int(amount))

def callback(ch, method, properties, body):
    params = body.decode().split(",")
    print("payment callback: " + body.decode())
    if params[0] == "add":
        add_credit(params[1], params[2])
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue="payment", on_message_callback=callback)
channel.start_consuming()