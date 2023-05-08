import json

class Order:
    order_id: int
    user_id: int
    items: list[str]
    paid: bool


    def __init__(self, order_id: int, user_id: int, items: list[str], paid:bool = False):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.paid = paid

    def to_redis_input(self) -> dict:
        resultDict = self.__dict__
        resultDict['paid'] = int(resultDict['paid'])
        resultDict['items'] = json.dumps(resultDict['items'])
        return resultDict
    
    def bytes_to_order(order_id: int, order_bytes: list[bytes]):
        user_id = int(order_bytes[0])
        items = json.loads(order_bytes[1])
        paid = bool(int(order_bytes[2]))
        return Order(order_id, user_id, items, paid)