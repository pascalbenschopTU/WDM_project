docker-compose exec -T payment_configsvr01 sh -c "mongosh < payment/scripts/init-configserver.js"
docker-compose exec -T payment_shard01-a sh -c "mongosh < payment/scripts/init-shard01.js"
docker-compose exec -T payment_shard02-a sh -c "mongosh < payment/scripts/init-shard02.js"
docker-compose exec -T payment_shard03-a sh -c "mongosh < payment/scripts/init-shard03.js"

# Wait for config server and shards to elect primaries
sleep 20
# Initializing the router
docker-compose exec -T payment_router01 sh -c "mongosh < payment/scripts/init-router.js"

# Enable sharding and setup sharding-key

docker-compose exec -T payment_router01 mongosh --port 27017

docker-compose exec -T payment_router01 sh -c "mongosh < payment/scripts/init-mongo.js"

