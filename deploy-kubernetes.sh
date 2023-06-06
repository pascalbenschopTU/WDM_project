minikube start

ECHO "Installing ingress...."

helm install -f helm-config/nginx-helm-values.yaml nginx ingress-nginx/ingress-nginx
    

while [ -z $(kubectl get pod -o=name --field-selector status.phase==Running) ]
do
    ECHO "Waiting for ingress to start.....";
    sleep 5
done

ECHO "Ingress started!"

ECHO "Waiting for ingress to start properly"
sleep 20

ECHO "Applying k8s ymls...."

$(kubectl apply -f .\\test2\\)

while [ ! -z "$(kubectl get pod -o=name --field-selector status.phase!=Running)" ]
do
    ECHO "Waiting pods to start.....";
    sleep 5
done

sleep 5
ECHO "Setting up the mongo databases";

sh .\\database_setup_k8s.sh
ECHO "Done!"

minikube tunnel