# Web-scale Data Management Project

### Project structure

- `env`
  Folder containing the Redis env variables for the docker-compose deployment
- `helm-config`
  Helm chart values for Redis and ingress-nginx
- `k8s`
  Folder containing the kubernetes deployments, apps and services for the ingress, order, payment and stock services.
- `order`
  Folder containing the order application logic and dockerfile.
- `payment`
  Folder containing the payment application logic and dockerfile.
- `stock`
  Folder containing the stock application logic and dockerfile.
- `test`
  Folder containing some basic correctness tests for the entire system. (Feel free to enhance them)

### Deployment types:

#### docker-compose (local development)

First run `docker-compose up --build` to get all the web services running, then run `payment_database_setup.sh` to initialize the sharding of the payment database. You only need to run the setup script once.

**_Requirements:_** You need to have docker and docker-compose installed on your machine.

#### minikube (local k8s cluster)

- install minikube
- add helm to path

Run the following commands to set up a local cluster:

```
minikube start
```

Install ingress and rabbitmq
```
helm install -f helm-config/nginx-helm-values.yaml nginx ingress-nginx/ingress-nginx

helm upgrade --install -f helm-config/rabbitmq-helm-values.yaml rabbitmq oci://registry-1.docker.io/bitnamicharts/rabbitmq
```
If helm cannot find ingress-nginx: `helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx`

Pull order-service (can also be done without docker)
```
& minikube -p minikube docker-env --shell powershell | Invoke-Expression (temporarily for pulling image)

docker-compose build rabbitmq (temporarily for pulling image)

docker-compose build order-service (temporarily for pulling image)

kubectl apply -f .\k8s_final\ (will be renamed)
```

Wait for the ingress to be ready, repeat `kubectl get pods` until all ready.`


```
database_setup_k8s.sh

minikube tunnel
```

MongoServerError: Rejecting initiate with a set name that differs from command line set name, initiate set name: rs-order_shard-03, command line set name: order_rs-shard-03

The application should now be avaibable on `localhost`. You can reach it by using curl:

F.e.:

`curl -i -X POST http://localhost/payment/create_user` 

**_Requirements:_** You need to have minikube (with ingress enabled) and helm installed on your machine.

#### kubernetes cluster (managed k8s cluster in the cloud)

Similarly to the `minikube` deployment but run the `deploy-charts-cluster.sh` in the helm step to also install an ingress to the cluster.

**_Requirements:_** You need to have access to kubectl of a k8s cluster.
