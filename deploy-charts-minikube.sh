#!/usr/bin/env bash

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install -f helm-config/redis-helm-values.yaml redis bitnami/redis
helm install -f helm-config/postgres-helm-values.yaml postgres bitnami/postgresql
helm install -f helm-config/rabbitmq-helm-values.yaml rabbitmq bitnami/rabbitmq
helm install -f helm-config/mongo-helm-values.yaml mongo bitnami/mongodb