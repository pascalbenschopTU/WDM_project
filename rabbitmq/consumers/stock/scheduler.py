# import pika
from sqlalchemy import create_engine, text
import os
from stock_item import AddStatement, SubtractTansaction, StockItem, Statement, SelectStatement
from typing import Union
import asyncio
import aioamqp
import threading
from aio_pika import Message, connect, ExchangeType
from aioamqp.channel import Channel
from aio_pika.abc import AbstractIncomingMessage

operations_queue = asyncio.Queue()
global_channel = None        
        #setup database
connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(connection_string)


# operations: list[Union[SelectStatement, AddStatement, SubtractTansaction]]  = []

def convert_to_transaction(queue_identifier: str, correlation_id: str, csv_items: list[str]) -> SubtractTansaction:
    statements = []
    for i in range(0, len(csv_items), 2):
        (id, amount) = (csv_items[i], csv_items[i+1])
        statements.append(Statement(id, int(amount)))
    return SubtractTansaction(queue_identifier, correlation_id, statements)

def get_items(ids: list[str], db_connection) -> dict[str, StockItem]:
    select_statement = text("SELECT * FROM stock WHERE id=ANY(:ids)")
    unique_ids = list(set(ids))
    items: dict[StockItem] = {}
    rows = db_connection.execute(select_statement, {"ids": unique_ids})
    for row in rows:
        items[row[0]] = StockItem(row[0], int(row[1]), int(row[2]))
    return items

def persist_transactions(items: list[StockItem], db_connection):
    with engine.connect() as db_connection:
        for item in items:
            update_statement = text("UPDATE stock SET stock = :stock WHERE id=:id;")
            db_connection.execute(update_statement, {"id": id, "stock": item.stock})
    
async def execute_transactions(transactions: list[Union[SelectStatement, AddStatement, SubtractTansaction]], items: dict[str, StockItem]):
    for transaction in transactions:
        if isinstance(transaction, SelectStatement):
            item = items[transaction.item_id]
            message = f"Could not find item with id: {transaction.item_id}"
            if item is not None:
                message = item.convert_to_json_string()
            await send_response(transaction.reply_to, transaction.correlation_id, message) #message
        elif isinstance(transaction, AddStatement):
            items[transaction.item_id] += transaction.amount
        elif isinstance(transaction, SubtractTansaction):
            items_clone = items
            all_successfull = True
            for statement in transaction.statements:
                if items[statement.item_id] >= statement.amount:
                    items_clone[statement.item_id] = items[statement.item_id] - statement.amount
                else:
                    await send_response(transaction.reply_to, transaction.correlation_id, f"Not enough stock of {statement.item_id}")
                    all_successfull = False
                    break
            if all_successfull:
                items = items_clone
                await send_response(transaction.reply_to, transaction.correlation_id, "Success")
    return items
    
async def execute_window(transactions: list[Union[SelectStatement, AddStatement, SubtractTansaction]]) -> None:
    # global operations
    # transactions = operations       
    # await send_response(str(transactions[0].reply_to), str(transactions[0].correlation_id), str(transactions[0].item_id))
    ids = set()
    for entry in transactions:
        if isinstance(entry, SubtractTansaction):
            for statement in entry.statements:
                ids.add(statement.item_id)
        else:
            ids.add(entry.item_id)
    ids = list(ids)
    with engine.connect() as db_connection:
        items = get_items(ids, db_connection)
        updated_items = await execute_transactions(transactions, items)
        to_persist = []
        for key, item in items.items():
            if item.stock != updated_items[key].stock:
                to_persist.append(updated_items[key])
        persist_transactions(to_persist, db_connection)
        db_connection.commit()

async def read_array_periodically(interval):
    while True:
        transactions = []
        while not operations_queue.empty():
            queue_object = await operations_queue.get()
            transactions.append(queue_object)
    
        if len(transactions) > 0:
            await execute_window(transactions)

        await asyncio.sleep(interval)


def start_reading_loop():
    asyncio.run(read_array_periodically(0.01))

async def send_response(reply_to: str, correlation_id: str, out_going_message: str):
    global global_channel
    message = Message(body=out_going_message.encode(), correlation_id=correlation_id) #.encode()
    await global_channel.default_exchange.publish(message, routing_key=reply_to)


async def select_callback(message: AbstractIncomingMessage):
    async with message.process():
        # only item_id is sent
        select_statement = SelectStatement(message.body.decode(), message.reply_to, message.correlation_id)
        await operations_queue.put(select_statement)
        # await send_response(message.reply_to, message.correlation_id, message.body)

async def new_item_callback(ch, body, envelope, properties):
            (id, price) = body.decode().split(",")
            with engine.connect().execution_options(isolation_level="READ UNCOMMITTED") as db_connection:
                statement = text("INSERT INTO stock (id, price, stock) VALUES (:id, :price, 0);")
                db_connection.execute(statement, {"price": price, "id": id})
                db_connection.commit()
                await ch.basic_ack(delivery_tag = envelope.delivery_tag)

async def add_stock_callback(ch, body, envelope, properties):
            (item_id, amount) = body.decode().split(",")
            add_statement = AddStatement(item_id, amount, properties.reply_to, properties.correlation_id)
            # operations.append(add_statement)
            await operations_queue.put(add_statement)
            
async def subtract_transaction_callback(ch, body, envelope, properties):
            params = body.decode().split(",") #It's item_id, amount item_id amount.... yadada
            transaction = convert_to_transaction(properties.reply_to, properties.correlation_id, params)
            # operations.append(transaction)
            await operations_queue.put(transaction)




# async def send_response(reply_to, correlation_id, message):
#     global channel
#     rabbitmq_message = Message(
#             message, correlation_id=correlation_id
#         )
#     await channel.default_exchange.publish(
#             rabbitmq_message,
#             routing_key=reply_to,
#         )

async def main() -> None:
    connection = await connect(f"amqp://guest:guest@rabbitmq/")
    async with connection:
        channel = await connection.channel()
        global global_channel
        global_channel = channel
        select = "select"
        select_exchange = await channel.declare_exchange(select, ExchangeType.FANOUT, durable=True)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(select_exchange)
        await queue.consume(select_callback)
    
        subtract = "subtract"
        subtract_exchange = await channel.declare_exchange(subtract, ExchangeType.FANOUT, durable=True)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(subtract_exchange)
        await queue.consume(subtract_transaction_callback, no_ack=True)
            
        add = "add"
        add_exchange = await channel.declare_exchange(add, ExchangeType.FANOUT, durable=True)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(add_exchange)
        await queue.consume(add_stock_callback, no_ack=True)
                
        new_items = "new_items"
        new_item_exchange = await channel.declare_exchange(new_items, ExchangeType.FANOUT, durable=True)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(new_item_exchange)
        await queue.consume(new_item_callback, no_ack=True)
        
        asyncio.create_task(read_array_periodically(0.01))
        await asyncio.Future()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.run(main())
    
    
    
# def select_callback(ch, method, properties, body):
#     # only item_id is sent
#     select_statement = SelectStatement(body.decode(), properties.reply_to, properties.correlation_id)
#     operations.append(select_statement)
    
#     # send_response(operations[0].reply_to, operations[0].correlation_id, "hello")
    
# select = "select"
# channel.exchange_declare(exchange=select, exchange_type='fanout', durable=True)
# result = channel.queue_declare(queue='', durable=True)
# queue_name = result.method.queue
# channel.queue_bind(exchange=select, queue=queue_name)
# channel.basic_consume(queue=queue_name, on_message_callback=select_callback, auto_ack=True)

# def subtract_transaction_callback(ch, method, properties, body):
#     params = body.decode().split(",") #It's item_id, amount item_id amount.... yadada
#     transaction = convert_to_transaction(properties.reply_to, properties.correlation_id, params)
#     operations.append(transaction)
#     operations_queue.put(transaction)
    
# subtract = "subtract"
# channel.exchange_declare(exchange=subtract, exchange_type='fanout', durable=True)
# result = channel.queue_declare(queue='', durable=True)
# queue_name = result.method.queue
# channel.queue_bind(exchange=subtract, queue=queue_name)
# channel.basic_consume(queue=queue_name, on_message_callback=subtract_transaction_callback, auto_ack=True)
    
# def add_stock_callback(ch, method, properties, body):
#     (item_id, amount) = body.decode().split(",")
#     add_statement = AddStatement(item_id, amount, properties.reply_to, properties.correlation_id)
#     operations.append(add_statement)
#     operations_queue.put(add_statement)

# add = "add"
# channel.exchange_declare(exchange=add, exchange_type='fanout', durable=True)
# result = channel.queue_declare(queue='', durable=True)
# queue_name = result.method.queue
# channel.queue_bind(exchange=add, queue=queue_name)
# channel.basic_consume(queue=queue_name, on_message_callback=add_stock_callback, auto_ack=True)

# # new items queue
# def new_item_callback(ch, method, properties, body):
#     (id, price) = body.decode().split(",")
#     with engine.connect().execution_options(isolation_level="READ UNCOMMITTED") as db_connection:
#         statement = text("INSERT INTO stock (id, price, stock) VALUES (:id, :price, 0);")
#         db_connection.execute(statement, {"price": price, "id": id})
#         db_connection.commit()
#         ch.basic_ack(delivery_tag = method.delivery_tag)
   
# new_items = "new_items"
# channel.exchange_declare(exchange=new_items, exchange_type='fanout', durable=True)
# result = channel.queue_declare(queue='', durable=True)
# queue_name = result.method.queue
# channel.queue_bind(exchange=new_items, queue=queue_name)
# channel.basic_consume(queue=queue_name, on_message_callback=new_item_callback)