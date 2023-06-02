import json
import sys

class Order:
    order_id: int
    user_id: int
    items: dict
    total_price: int
    paid: bool


    def __init__(self, order_id: int, user_id: int, items: dict = {}, total_price: int = 0, paid: bool = False):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total_price = total_price
        self.paid = paid

    def create_empty(user_id: int):
        return {'user_id': user_id, "items": {}, "total_price": 0, "paid": False}
    
    def to_mongo_input(self) -> dict:
        print(self, file=sys.stderr)
        return {'user_id': self.user_id, 'items': self.items, 'total_price': self.total_price, 'paid': self.paid}
    
    def to_response(self) -> dict:
        return {'order_id': str(self.order_id), 'user_id': self.user_id, 'items': self.items, 'total_price': self.total_price, 'paid': self.paid}
    
    def from_mongo_output(order_dict: dict):
        order_id = order_dict['_id']
        user_id = order_dict['user_id']
        items = order_dict['items']
        total_price = order_dict['total_price']
        paid = order_dict['paid']
        return Order(order_id, user_id, items, total_price, paid)
