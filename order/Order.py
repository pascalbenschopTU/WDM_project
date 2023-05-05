import json

class Order:
    order_id: int
    user_id: int
    items: dict
    paid: bool


    def __init__(self, order_id: int, user_id: int, items: dict = {}, paid:bool = False):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.paid = paid

    def to_redis_input(self) -> dict:
        resultDict = self.__dict__
        resultDict['paid'] = 1 if resultDict['paid'] else 0
        resultDict['items'] = json.dumps(resultDict['items'])
        return resultDict
    
    def bytes_to_order(order_id: int, order_bytes: list[bytes]):
        user_id = int(order_bytes[0])
        items = json.loads(order_bytes[1])
        paid = True if int(order_bytes[2]) == 1 else False
        return Order(order_id, user_id, items, paid)
