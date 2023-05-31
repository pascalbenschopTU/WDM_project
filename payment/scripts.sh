docker-compose up -d

# Initialize the replica sets (config servers and shards) 
docker-compose exec configsvr01 sh -c "mongosh < /scripts/init-configserver.js"
docker-compose exec shard01-a sh -c "mongosh < /scripts/init-shard01.js"
docker-compose exec shard02-a sh -c "mongosh < /scripts/init-shard02.js"
docker-compose exec shard03-a sh -c "mongosh < /scripts/init-shard03.js"

# Initializing the router
docker-compose exec router01 sh -c "mongosh < /scripts/init-router.js"

# Enable sharding and setup sharding-key
docker-compose exec router01 mongosh --port 27017

sh.enableSharding("payment_mongodb")
db.adminCommand( { shardCollection: "payment_mongodb.users", key: { user_id: "hashed" } } )
db.adminCommand( { shardCollection: "payment_mongodb.paid_orders", key: { order_id: "hashed" } } )

db.createUser({
  user: 'user',
  pwd: 'password',
  roles: [
    {
      role: 'readWrite',
      db: 'payment_mongodb',
    },
  ],
});
