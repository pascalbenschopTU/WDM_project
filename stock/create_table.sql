\c stock
CREATE TABLE stock (
    id SERIAL PRIMARY KEY,
    price INT NOT NULL,
    stock INT NOT NULL
);

CREATE TABLE idempotency_keys (
    idempotency_key TEXT NOT NULL PRIMARY KEY,
);