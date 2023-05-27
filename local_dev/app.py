
from typing import List
from sqlalchemy import create_engine, text
# connection_string = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"

connection_string = "postgresql+psycopg2://testuser:qwerty@localhost:5432/stock"
engine = create_engine(connection_string)
with engine.connect() as connection:
    create_table = text("CREATE TABLE IF NOT EXISTS stock (id VARCHAR PRIMARY KEY, price INT NOT NULL, stock INT NOT NULL);")
    response = connection.execute(create_table)
    create_item = text("INSERT INTO stock (id, price, stock) values (:id, :price, :amount)")
    create_item_result = connection.execute(create_item, {"id": "abc", "price": 1, "amount": 1})
    statement = text("SELECT * FROM stock WHERE id = :id")
    result = connection.execute(statement, {"id": "abc"})
    for row in result:
        id = row[0]
        price= row[1]
        stock=row[2]
    print("done")
