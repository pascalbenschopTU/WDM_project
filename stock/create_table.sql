\c stock
DROP TABLE stock;
CREATE TABLE stock (
    id VARCHAR PRIMARY KEY,
    price INT NOT NULL,
    stock INT NOT NULL
);