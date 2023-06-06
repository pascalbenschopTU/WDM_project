sh.enableSharding("payment_mongodb");
db.adminCommand({
  shardCollection: "payment_mongodb.users",
  key: { user_id: "hashed" },
});
db.adminCommand({
  shardCollection: "payment_mongodb.paid_orders",
  key: { order_id: "hashed" },
});

db.adminCommand({
  shardCollection: "payment_mongodb.idempotency_keys",
  key: { idempotency_key: "hashed" },
});

db.createUser({
  user: "user",
  pwd: "password",
  roles: [
    {
      role: "readWrite",
      db: "payment_mongodb",
    },
  ],
});
