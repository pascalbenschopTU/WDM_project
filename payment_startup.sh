docker-compose exec -T configsvr01 sh -c "mongosh < payment/scripts/init-configserver.js"
docker-compose exec -T shard01-a sh -c "mongosh < /payment/scripts/init-shard01.js"
docker-compose exec -T shard02-a sh -c "mongosh < payment/scripts/init-shard02.js"
docker-compose exec -T shard03-a sh -c "mongosh < payment/scripts/init-shard03.js"

# Wait for config server and shards to elect primaries
sleep 20
# Initializing the router
docker-compose exec -T router01 sh -c "mongosh < payment/scripts/init-router.js"

# Enable sharding and setup sharding-key

docker-compose exec -T router01 mongosh --port 27017

docker-compose exec -T router01 sh -c "mongosh < payment/scripts/init-mongo.js"

