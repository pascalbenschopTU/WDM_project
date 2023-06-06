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

Install ingress via helm
```
helm install -f helm-config/nginx-helm-values.yaml nginx ingress-nginx/ingress-nginx
```
Wait for the ingress to be ready, repeat `kubectl get pods` until all ready 1/1.`

If helm cannot find ingress-nginx: `helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx`

# setup redis
helm repo add bitnami https://charts.bitnami.com/bitnami

```
helm install my-release --set usePassword=false oci://registry-1.docker.io/bitnamicharts/redis-cluster
```
Check they are running: `kubectl get pods`

# build images with minikube
Apply the k8s scripts
```
kubectl apply -f .\test2\ (will be renamed)
```
Again, wait for the containers to be ready, repeat `kubectl get pods` until all ready 1/1.`

Then run database setup for mongo shards, and when finished start the tunnel
```
database_setup_k8s.sh

minikube addons enable ingress

minikube tunnel
```
The application should now be avaibable on `localhost`. You can reach it by using curl:

F.e.:

`curl -i -X POST http://localhost/payment/create_user` 

**_Requirements:_** You need to have minikube (with ingress enabled) and helm installed on your machine.

#### kubernetes cluster (managed k8s cluster in the cloud)

Similarly to the `minikube` deployment but run the `deploy-charts-cluster.sh` in the helm step to also install an ingress to the cluster.

**_Requirements:_** You need to have access to kubectl of a k8s cluster.
