Green='\033[0;32m'
Color_Off='\033[0m'

ECHO -e "${Green} Setting up shards for the databases ${Color_Off}" > `tty`
ECHO -e "${Green} Setting up shards for order database.... ${Color_Off}" > `tty`
pc01=$(kubectl get pods -o=name | grep order-configserver01 | sed "s/^.\{4\}//")
kubectl exec --tty $pc01 -- sh -c "mongosh --eval '`cat ./order/scripts/init-configserver.js`'"
 
ps01=$(kubectl get pods -o=name | grep order-shard01-a | sed "s/^.\{4\}//")
kubectl exec --tty $ps01 -- sh -c "mongosh --eval '`cat ./order/scripts/init-shard01.js`'"

ps02=$(kubectl get pods -o=name | grep order-shard02-a | sed "s/^.\{4\}//")
kubectl exec --tty $ps02 -- sh -c "mongosh --eval '`cat ./order/scripts/init-shard02.js`'"

ps03=$(kubectl get pods -o=name | grep order-shard03-a | sed "s/^.\{4\}//")
kubectl exec --tty $ps03 -- sh -c "mongosh --eval '`cat ./order/scripts/init-shard03.js`'"

ECHO -e "${Green} Setting up shards for payment database.... ${Color_Off}" > `tty`
pc01=$(kubectl get pods -o=name | grep payment-configsvr01 | sed "s/^.\{4\}//")
kubectl exec --tty $pc01 -- sh -c "mongosh --eval '`cat ./payment/scripts/init-configserver.js`'"
 
ps01=$(kubectl get pods -o=name | grep payment-shard01-a | sed "s/^.\{4\}//")
kubectl exec --tty $ps01 -- sh -c "mongosh --eval '`cat ./payment/scripts/init-shard01.js`'"

ps02=$(kubectl get pods -o=name | grep payment-shard02-a | sed "s/^.\{4\}//")
kubectl exec --tty $ps02 -- sh -c "mongosh --eval '`cat ./payment/scripts/init-shard02.js`'"

ps03=$(kubectl get pods -o=name | grep payment-shard03-a | sed "s/^.\{4\}//")
kubectl exec --tty $ps03 -- sh -c "mongosh --eval '`cat ./payment/scripts/init-shard03.js`'"

# Setup shards for order database


ECHO -e "${Green} Done setting up shards for the databases! ${Color_Off}" > `tty`

# Wait for config server and shards to elect primaries
sleep 20

ECHO -e "${Green} Setting up routers for the database ${Color_Off}" > `tty`

# # # Initializing the router
# # #Enable sharding and setup sharding-key
ECHO -e "${Green} Setting the router for the order servive..... ${Color_Off}" > `tty`

pr01=$(kubectl get pods -o=name | grep payment-router01 | sed "s/^.\{4\}//")
kubectl exec --tty $pr01 -- sh -c "mongosh --eval '`cat ./payment/scripts/init-router.js`'"
kubectl exec --tty $pr01 -- sh -c "mongosh --eval '`cat ./payment/scripts/init-mongo.js`'"

pr01=$(kubectl get pods -o=name | grep order-router01 | sed "s/^.\{4\}//")
kubectl exec --tty $pr01 -- sh -c "mongosh --eval '`cat ./order/scripts/init-router.js`'"
kubectl exec --tty $pr01 -- sh -c "mongosh --eval '`cat ./order/scripts/init-mongo.js`'"

ECHO -e "${Green} Done settting up the routers! ${Color_Off}" > `tty`
sleep 20