from enum import Enum

class Operator(Enum):
    SUBTRACT = 1,
    ADD = 2,
    SELECT = 3
    

class Statement():
    item_id: str
    amount: int
    
    def __init__(self, item_id: str, amount: int):
        self.item_id = item_id
        self.amount = amount

class SubtractTansaction():
    reply_to: str
    statements: list[Statement]
    correlation_id: str
    
    def __str__(self):
        return_string = ""
        for statement in self.statements:
            return_string += "{" + f"item_id: {statement.item_id}, amount: {statement.amount}" + "},"
        return return_string
    
    def __init__(self, reply_to: str, correlation_id: str, statements: list[Statement] = []):
        self.reply_to = reply_to
        self.correlation_id = correlation_id
        self.statements = statements

class SelectStatement():
    item_id: str
    reply_to: str
    correlation_id: str
    
    def __init__(self, item_id: str, reply_to: str, correlation_id: str):
        self.item_id = item_id
        self.reply_to = reply_to
        self.correlation_id = correlation_id

class AddStatement():
    item_id: str
    amount: int
    reply_to: str
    correlation_id: str
    
    def __init__(self, item_id: str, amount: int, reply_to: str, correlation_id: str):
        self.item_id = item_id
        self.amount = amount
        self.reply_to = reply_to
        self.correlation_id = correlation_id

class StockItem():
    item_id: str
    price: int
    stock: int
    
    def __init__(self, item_id: str, price: int, stock: int):
        self.item_id = item_id
        self.price = price
        self.stock = stock
    
    def convert_to_json_string(self):
        return f"item_id: {self.item_id}, 'price': {self.price}, stock: {self.stock}"
    