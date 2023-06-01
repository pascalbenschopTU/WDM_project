class Statement():
    item_id: str
    amount: int
    
    def __init__(self, item_id: str, amount: int):
        self.item_id = item_id
        self.amount = amount

class StockTransaction():
    transaction_id: str
    statements: list[Statement]
    correlation_id: str
    
    def __str__(self):
        return_string = ""
        for statement in self.statements:
            return_string += "{" + f"item_id: {statement.item_id}, amount: {statement.amount}" + "},"
        return return_string
    
    def __init__(self, transaction_id: str, correlation_id: str, statements: list[Statement] = []):
        self.transaction_id = transaction_id
        self.correlation_id = correlation_id
        self.statements = statements
