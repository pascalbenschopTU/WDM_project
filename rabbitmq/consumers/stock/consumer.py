import pika
import redis
import os

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


## define channels
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672))
channel = connection.channel()
channel.queue_declare(queue="stock", durable=True)

def add_stock(item_id: str, amount: int):
    db.hincrby(f'item:{item_id}', 'stock', int(amount))

def callback(ch, method, properties, body):
    params = body.decode().split(",")
    with open('/HOME/FLASK-APPlog.txt', 'a') as f:
    # Write some data to the file
        f.write(body.decode() + "\n")
    if params[0] == "inc":
        for i in range(1, len(params)):
            add_stock(params[i], 1)

    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue="stock", on_message_callback=callback)
channel.start_consuming()