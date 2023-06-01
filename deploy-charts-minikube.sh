#!/usr/bin/env bash

helm upgrade --install -f helm-config/postgres-helm-values.yaml postgres oci://registry-1.docker.io/bitnamicharts/postgresql
helm upgrade --install -f helm-config/rabbitmq-helm-values.yaml rabbitmq oci://registry-1.docker.io/bitnamicharts/rabbitmq
helm upgrade --install -f helm-config/mongo-helm-values.yaml mongo oci://registry-1.docker.io/bitnamicharts/mongodb