# Web-scale Data Management Project Template

Basic project structure with Python's Flask and Redis. 
**You are free to use any web framework in any language and any database you like for this project.**

### Project structure

* `env`
    Folder containing the Redis env variables for the docker-compose deployment
    
* `helm-config` 
   Helm chart values for Redis and ingress-nginx
        
* `k8s`
    Folder containing the kubernetes deployments, apps and services for the ingress, order, payment and stock services.
    
* `order`
    Folder containing the order application logic and dockerfile. 
    
* `payment`
    Folder containing the payment application logic and dockerfile. 

* `stock`
    Folder containing the stock application logic and dockerfile. 

* `test`
    Folder containing some basic correctness tests for the entire system. (Feel free to enhance them)

### Deployment types:

#### docker-compose (local development)

After coding the REST endpoint logic run `docker-compose up --build` in the base folder to test if your logic is correct
(you can use the provided tests in the `\test` folder and change them as you wish). 

***Requirements:*** You need to have docker and docker-compose installed on your machine.

#### minikube (local k8s cluster)

This setup is for local k8s testing to see if your k8s config works before deploying to the cloud. 
First deploy your database using helm by running the `deploy-charts-minicube.sh` file (in this example the DB is Redis 
but you can find any database you want in https://artifacthub.io/ and adapt the script). Then adapt the k8s configuration files in the
`\k8s` folder to mach your system and then run `kubectl apply -f .` in the k8s folder. 

***Requirements:*** You need to have minikube (with ingress enabled) and helm installed on your machine.

## Minikube Windows set up:
Go to a powershell terminal with admin rights and run the following commands:

`minikube start --driver=docker`

`.\deploy-charts-minicube.sh`

Then you can type `minikube docker-env` to get the command to set the docker environment variables. Copy and paste the command and run it.
Or you could directly run: 

`& minikube -p minikube docker-env --shell powershell | Invoke-Expression`

Then in a seperate terminal that points to the same directory as the docker-compose.yml file run:

`docker-compose up -d --build`

Then in the first terminal run:

`minikube image ls --format table`

To check that the order, payment and stock images are there.

Then run:

`kubectl apply -f .\k8s\`

And check if the services are running with:

`kubectl get pods`

You should see READY 1/1 for every pod.

### Troubleshooting:

To delete pvc's run `helm list` and then `helm delete <name>` for each pvc.
To delete pvc's by force from kubectl use `delete pvc --all --force`
To check the logs of kubectl use `kubectl logs <pod-name>`, for example `kubectl logs stock-deployment-b8d664cb5-bbnk8`

### kubernetes cluster (managed k8s cluster in the cloud)

Similarly to the `minikube` deployment but run the `deploy-charts-cluster.sh` in the helm step to also install an ingress to the cluster. 

***Requirements:*** You need to have access to kubectl of a k8s cluster.
