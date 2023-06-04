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

Run the following commands to set up a local cluster:

`minikube start`

`helm install -f helm-config/nginx-helm-values.yaml nginx ingress-nginx/ingress-nginx`

`kubectl apply -f ./test2/` (will be renamed)

`minikube tunnel`

The application should now be avaibable on `localhost`. You can reach it by using curl:

F.e.:
`curl -i -X POST http://localhost/payment/create_user` 

**_Requirements:_** You need to have minikube (with ingress enabled) and helm installed on your machine.

#### kubernetes cluster (managed k8s cluster in the cloud)

Similarly to the `minikube` deployment but run the `deploy-charts-cluster.sh` in the helm step to also install an ingress to the cluster.

**_Requirements:_** You need to have access to kubectl of a k8s cluster.
