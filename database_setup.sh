#!/usr/bin/env bash
Green='\033[0;32m'
Color_Off='\033[0m'

ECHO -e "${Green} Setting up shards for the databases ${Color_Off}" > `tty`
ECHO -e "${Green} Setting up shards for order database.... ${Color_Off}" > `tty`
docker-compose exec -T order_configserver01 sh -c "mongosh < order/scripts/init-configserver.js"
docker-compose exec -T order_shard01-a sh -c "mongosh < /order/scripts/init-shard01.js"
docker-compose exec -T order_shard02-a sh -c "mongosh < order/scripts/init-shard02.js"
docker-compose exec -T order_shard03-a sh -c "mongosh < order/scripts/init-shard03.js"

ECHO -e "${Green} Setting up shards for payment database.... ${Color_Off}" > `tty`
docker-compose exec -T payment_configsvr01 sh -c "mongosh < payment/scripts/init-configserver.js"
docker-compose exec -T payment_shard01-a sh -c "mongosh < payment/scripts/init-shard01.js"
docker-compose exec -T payment_shard02-a sh -c "mongosh < payment/scripts/init-shard02.js"
docker-compose exec -T payment_shard03-a sh -c "mongosh < payment/scripts/init-shard03.js"

ECHO -e "${Green} Done setting up shards for the databases! ${Color_Off}" > `tty`

# Wait for config server and shards to elect primaries
sleep 20

ECHO -e "${Green} Setting up routers for the database ${Color_Off}" > `tty`

# Initializing the router
#Enable sharding and setup sharding-key
ECHO -e "${Green} Setting the router for the order servive..... ${Color_Off}" > `tty`
docker-compose exec -T order_router01 sh -c "mongosh < order/scripts/init-router.js"
docker-compose exec -T order_router01 sh -c "mongosh < order/scripts/init-mongo.js"

ECHO -e "${Green} Setting the router for the payment servive..... ${Color_Off}" > `tty`

docker-compose exec -T payment_router01 sh -c "mongosh < payment/scripts/init-router.js"
docker-compose exec -T payment_router01 sh -c "mongosh < payment/scripts/init-mongo.js"

ECHO -e "${Green} Done settting up the routers! ${Color_Off}" > `tty`