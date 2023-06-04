# import pika
import os
from stock_item import AddStatement, SubtractTansaction, StockItem, Statement, SelectStatement
from typing import Union
import asyncio
from aio_pika import Message, connect, ExchangeType
from aio_pika.abc import AbstractIncomingMessage
from aioredlock import Aioredlock, LockError
from redis import asyncio as aioredis
from aio_pika.pool import Pool
import aio_pika
import json

operations_queue = asyncio.Queue()
global_channel = None        

host = os.environ['REDIS_HOST']
port = port=int(os.environ['REDIS_PORT'])
password = password=os.environ['REDIS_PASSWORD']
db =int(os.environ['REDIS_DB'])
queue_name = os.environ['QUEUE_NAME']
# Define a list of connections to your Redis instances:
connection_url = f"redis://default:{password}@{host}:{port}"

redis_instances = [
  connection_url
]
RABBIT_URI = "amqp://guest:guest@rabbitmq/"
lock_manager = Aioredlock(redis_instances)

def convert_to_transaction(queue_identifier: str, correlation_id: str, csv_items: list[str]) -> SubtractTansaction:
    statements = []
    for i in range(0, len(csv_items), 2):
        (id, amount) = (csv_items[i], csv_items[i+1])
        statements.append(Statement(id, int(amount)))
    return SubtractTansaction(queue_identifier, correlation_id, statements)

## TODO do multiple fetches when i figure out how
async def get_items(ids: list[str], redis) -> dict[str, StockItem]:
    unique_ids = list(set(ids))
    # rows = redis.mget(unique_ids)
    items: dict[StockItem] = {}
    for id in unique_ids:
        item = await redis.hmget(f'item:{id}', 'price', 'stock')
        if None not in item:
            items[id] = (StockItem(id, int(item[0]), int(item[1])))
    return items

async def persist_transactions(items: dict[str, int], redis):
    async with redis.pipeline() as pipe:
        for key, stock in items.items():
            pipe.hincrby(f'item:{key}', 'stock', stock)
        await pipe.execute()

async def super_callback(message: AbstractIncomingMessage):
    async with message.process():
        params = message.body.decode().split(",")
        match params[0]:
            case "select":
                select_statement = SelectStatement(params[1], message.reply_to, message.correlation_id)
                await operations_queue.put(select_statement)
            case "add":
                (item_id, amount) = params[1:]
                add_statement = AddStatement(item_id, int(amount))
                await operations_queue.put(add_statement)
            case "subtract":
                params = params[1:] #It's item_id, amount item_id amount.... yadada
                transaction = convert_to_transaction(message.reply_to, message.correlation_id, params)
                await operations_queue.put(transaction)
   
async def new_item_callback(message: AbstractIncomingMessage):
    async with message.process(ignore_processed=True):
        (id, price) = message.body.decode().split(",")
        redis = aioredis.from_url(connection_url)
        item = {'item_id': id, 'price': price, 'stock': 0}
        await redis.hset(f'item:{id}', mapping=item) ## apparently need to await
        ## TODO fix this so we only send an ack if it works.
        await message.ack()


async def acquire_lock(ressource_name):
        global lock_manager
        try:
            lock = await lock_manager.lock(ressource_name, lock_timeout=10)
            return lock
        except LockError:
            print('Lock not acquired')
        raise

async def get_connection():
        return await aio_pika.connect_robust(RABBIT_URI)
    
async def main() -> None:
    loop = asyncio.get_event_loop()
    connection_pool = Pool(get_connection, max_size=3)
    async def get_channel() -> aio_pika.Channel:
        async with connection_pool.acquire() as connection:
            return await connection.channel()
        
    channel_pool = Pool(get_channel, max_size=10, loop=loop)
    
    async with channel_pool.acquire() as channel:
        await channel.set_qos(10)   
        global global_channel
        global_channel = channel
        
        requests = "requests"
        rquest_exchange = await channel.declare_exchange(requests, ExchangeType.FANOUT, durable=True)
        queue = await channel.declare_queue(queue_name, auto_delete=False, durable=True)
        await queue.bind(rquest_exchange)
        await queue.consume(super_callback)
        
    async with channel_pool.acquire() as channel:
        await channel.set_qos(1)
        new_items = "new_items"
        new_item_exchange = await channel.declare_exchange(new_items, ExchangeType.FANOUT, durable=True)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(new_item_exchange)
        await queue.consume(new_item_callback)
        
    
    ## Initiliaze redis
    
    redis_connection_pool = aioredis.ConnectionPool.from_url(connection_url, max_connections=10, encoding="utf-8", decode_responses=True)
    redis = aioredis.Redis(connection_pool=redis_connection_pool)
    
    async def send_response(reply_to: str, correlation_id: str, out_going_message: str):
        async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
            message = Message(body=out_going_message.encode(), correlation_id=correlation_id)
            await channel.default_exchange.publish(message, routing_key=reply_to)
    
    async def execute_window(transactions: list[Union[SelectStatement, AddStatement, SubtractTansaction]], redis) -> None:
        ids = set()
        for entry in transactions:
            if isinstance(entry, SubtractTansaction):
                for statement in entry.statements:
                    ids.add(statement.item_id)
            else:
                ids.add(entry.item_id)
        ids = list(ids)
        tasks = []
        for id in ids:
            tasks.append(asyncio.create_task(acquire_lock(id)))
        locks = await asyncio.gather(*tasks)
        
        items = await get_items(ids, redis)
        updated_items = await execute_transactions(transactions, items)
            
        await persist_transactions(updated_items, redis)
        for lock in locks:
            await lock_manager.unlock(lock)


    async def read_array_periodically(interval, redis):
        while True:
            transactions = []
            while not operations_queue.empty():
                queue_object = await operations_queue.get()
                transactions.append(queue_object)
        
            if len(transactions) > 0:
                await execute_window(transactions, redis)

            await asyncio.sleep(interval)
    
    async def execute_transactions(transactions: list[Union[SelectStatement, AddStatement, SubtractTansaction]], items_arg: dict[str, StockItem]):
        items = items_arg.copy()
        updated_stock = {}
        for transaction in transactions:
            if isinstance(transaction, SelectStatement):
                if transaction.item_id not in items.keys():
                    message = f"Could not find item with id: {transaction.item_id}status:400"
                    await send_response(transaction.reply_to, transaction.correlation_id, message)
                    break
                
                item = items[transaction.item_id]
                message = f"{json.dumps(item.__dict__)}status:200"
                await send_response(transaction.reply_to, transaction.correlation_id, message)
            
            elif isinstance(transaction, AddStatement):
                if transaction.item_id not in updated_stock.keys():
                    updated_stock[transaction.item_id] = 0
                items[transaction.item_id].stock += transaction.amount
                updated_stock[transaction.item_id] += transaction.amount
        
            elif isinstance(transaction, SubtractTansaction):
                items_clone = items.copy()
                updated_stock_clone = updated_stock.copy()
                all_successfull = True
                for statement in transaction.statements:
                    if items[statement.item_id].stock >= statement.amount:
                        if statement.item_id not in updated_stock_clone.keys():
                            updated_stock_clone[statement.item_id] = 0
                        items_clone[statement.item_id].stock -= statement.amount
                        updated_stock_clone[statement.item_id] -= statement.amount
                        
                    else:
                        await send_response(transaction.reply_to, transaction.correlation_id, f"Not enough stock of {statement.item_id}")
                        all_successfull = False
                        break
                if all_successfull:
                    items = items_clone
                    updated_stock = updated_stock_clone
                    await send_response(transaction.reply_to, transaction.correlation_id, "Success")
        return updated_stock
    
    task = loop.create_task(read_array_periodically(0.01, redis))    
    await task    
    await asyncio.Future()

    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
    