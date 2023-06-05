print("Started Creating User")

sh.enableSharding("order_mongodb")
db.adminCommand( { shardCollection: "order_mongodb.orders", key: { order_id: "hashed" } } )

db.createUser({
  user: 'user',
  pwd: 'password',
  roles: [
    {
      role: 'readWrite',
      db: 'order_mongodb',
    },
  ],
});

print("User created successfully")