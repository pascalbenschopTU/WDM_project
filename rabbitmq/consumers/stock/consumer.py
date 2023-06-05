# import pika
from stock_item import AddStatement, SubtractTansaction, StockItem, Statement, SelectStatement
from typing import Union
import asyncio
from aio_pika import Message, ExchangeType
from aio_pika.abc import AbstractIncomingMessage
from aioredlock import Aioredlock, LockError
from aio_pika.pool import Pool
import aio_pika
import json
import aioredis_cluster

operations_queue = asyncio.Queue()
global_channel = None        

# Define a list of connections to your Redis instances:
connection_urls = ["redis://redis-node-5", 
                   "redis://redis-node-1", 
                   "redis://redis-node-2", "redis://redis-node-3", 
                   "redis://redis-node-4", "redis://redis-node-0"
                   ]
RABBIT_URI = "amqp://guest:guest@rabbitmq/"
redis_global = None
prefetch_count = 1
def convert_to_transaction(queue_identifier: str, correlation_id: str, csv_items: list[str]) -> SubtractTansaction:
    statements = []
    for i in range(0, len(csv_items), 2):
        (id, amount) = (csv_items[i], csv_items[i+1])
        statements.append(Statement(id, int(amount)))
    return SubtractTansaction(queue_identifier, correlation_id, statements)



async def persist_transactions(items: dict[str, StockItem], redis):
    for key, stock in items.items():
        data = {'price': stock.price, 'stock': stock.stock}
        await redis.hset(f'item:{key}', value=json.dumps(data), field="key")

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

async def get_connection():
        return await aio_pika.connect_robust(RABBIT_URI)

async def connect_redis(connection_urls, counter):
        try:
            return await aioredis_cluster.create_redis_cluster(connection_urls)
        except:
            if counter > 10:
                return None
            await asyncio.sleep(0.1)
            await connect_redis(connection_urls, counter + 1)

async def main() -> None:
    loop = asyncio.get_event_loop()
    connection_pool = Pool(get_connection, max_size=3)
    
    redis = await connect_redis(connection_urls, 0)
    global redis_global
    redis_global = redis
    
    async def get_channel() -> aio_pika.Channel:
        async with connection_pool.acquire() as connection:
            return await connection.channel()
        
    channel_pool = Pool(get_channel, max_size=10, loop=loop)
    
    async with channel_pool.acquire() as channel:
        await channel.set_qos(prefetch_count)   
        global global_channel
        global_channel = channel
        
        requests = "requests"
        rquest_exchange = await channel.declare_exchange(requests, ExchangeType.FANOUT, durable=True)
        queue = await channel.declare_queue("request_queue_name", auto_delete=False, durable=True)
        await queue.bind(rquest_exchange)
        await queue.consume(super_callback)
        
    async def new_item_callback(message: AbstractIncomingMessage):
        async with message.process(ignore_processed=True):
            (id, price) = message.body.decode().split(",")
            global redis_global
            data = {'price': price, 'stock': 0}
            await redis_global.hset(f'item:{id}', value=json.dumps(data), field="key")
            await message.ack()
        
    async with channel_pool.acquire() as channel:
        await channel.set_qos(1)
        new_items = "new_items"
        new_item_exchange = await channel.declare_exchange(new_items, ExchangeType.FANOUT, durable=True)
        queue = await channel.declare_queue("item_queue_name", durable=True)
        await queue.bind(new_item_exchange)
        await queue.consume(new_item_callback)
        
    async def send_response(reply_to: str, correlation_id: str, out_going_message: str):
        async with channel_pool.acquire() as channel: 
            message = Message(body=out_going_message.encode(), correlation_id=correlation_id)
            await channel.default_exchange.publish(message, routing_key=reply_to)
    
    async def acquire_lock(ressource_name, lock_manager):
        try:
            lock = await lock_manager.lock(ressource_name, lock_timeout=10)
            return lock
        except LockError:
            print('Lock not acquired')
            raise
    
    async def get_items(ids: list[str], redis) -> dict[str, StockItem]:
        unique_ids = list(set(ids))
        items: dict[StockItem] = {}
        for id in unique_ids:
            item = await redis.hmget(f'item:{id}', field="key")
            if item[0] is not None:
                item = json.loads(str(item[0].decode()))
            if None not in item:
                items[id] = StockItem(id, int(item["price"]), int(item["stock"]))
        return items
    
    async def execute_window(transactions: list[Union[SelectStatement, AddStatement, SubtractTansaction]], redis) -> None:
        ## acquireing locks didn't work, so now we just imagine it worked
        # lock_manager = Aioredlock(connection_urls)
        ids = set()
        for entry in transactions:
            if isinstance(entry, SubtractTansaction):
                for statement in entry.statements:
                    ids.add(statement.item_id)
            else:
                ids.add(entry.item_id)
        ids = list(ids)
        # locks = []
        # try:
        #     for id in ids:
        #         lock = await acquire_lock(id, lock_manager)
        #         locks.append(lock)
        # except:
        #     for lock in locks:
        #         await lock_manager.unlock(lock)
        #         return
        #     if counter < 10:
        #         await asyncio.sleep(0.01)
        #         await execute_window(transactions, redis, counter + 1)
        #     else:
        #         for transaction in transactions:
        #             await operations_queue.put(transaction)
                
        items = await get_items(ids, redis)
        updated_items = await execute_transactions(transactions, items)
            
        await persist_transactions(updated_items, redis)
        # for lock in locks:
        #     await lock_manager.unlock(lock)

    async def read_transactions(interval, redis):
        while True:
            transactions = []
            if operations_queue.qsize() >= prefetch_count:
                for i in range(prefetch_count):
                    queue_object = await operations_queue.get()
                    transactions.append(queue_object)

            if len(transactions) > 0:
                await execute_window(transactions, redis)

            await asyncio.sleep(interval)
    
    async def execute_transactions(transactions: list[Union[SelectStatement, AddStatement, SubtractTansaction]], items_arg: dict[str, StockItem]):
        items = items_arg.copy()
        for transaction in transactions:
            if isinstance(transaction, SelectStatement):
                if transaction.item_id not in items.keys():
                    message = f"Couldn't find item {transaction.item_id}status:400"
                    await send_response(transaction.reply_to, transaction.correlation_id, message)
                    break
                
                item = items[transaction.item_id]
                if item is None or None:
                    message = f"item in keys, could not findstatus:400"
                    await send_response(transaction.reply_to, transaction.correlation_id, message)
                    break
                message = f"{json.dumps(item.__dict__)}status:200"
                await send_response(transaction.reply_to, transaction.correlation_id, message)
            
            elif isinstance(transaction, AddStatement):
                if transaction.item_id in items.keys():
                    items[transaction.item_id].stock += transaction.amount
        
            elif isinstance(transaction, SubtractTansaction):
                items_clone = items.copy()
                all_successfull = True
                for statement in transaction.statements:
                    if statement.item_id in items.keys() and items[statement.item_id].stock >= statement.amount:
                        items_clone[statement.item_id].stock -= statement.amount
                    else:
                        await send_response(transaction.reply_to, transaction.correlation_id, f"Not enough stock of {statement.item_id}")
                        all_successfull = False
                        break
                if all_successfull:
                    items = items_clone
                    await send_response(transaction.reply_to, transaction.correlation_id, "Success")
        return items
    
    task = loop.create_task(read_transactions(0.01, redis))
    await task    
    await asyncio.Future()

    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
    