echo "Setting up shards" > `tty`
docker-compose exec -T order_configserver01 sh -c "mongosh < order/scripts/init-configserver.js"
docker-compose exec -T order_shard01-a sh -c "mongosh < /order/scripts/init-shard01.js"
docker-compose exec -T order_shard02-a sh -c "mongosh < order/scripts/init-shard02.js"
docker-compose exec -T order_shard03-a sh -c "mongosh < order/scripts/init-shard03.js"

# Wait for config server and shards to elect primaries
echo "Setting up router" > `tty`
sleep 20
# Initializing the router
docker-compose exec -T order_router01 sh -c "mongosh < order/scripts/init-router.js"

Enable sharding and setup sharding-key

docker-compose exec -T order_router01 mongosh --port 27017

echo "Last command?" > `tty`

docker-compose exec -T order_router01 sh -c "mongosh < order/scripts/init-mongo.js"
echo "Done!" > `tty`
sleep 1000