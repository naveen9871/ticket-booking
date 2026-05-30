# Deployment Guide

## Local

```bash
docker compose up --build
```

Frontend: `http://localhost:3000`

Backend: `http://localhost:8001`

## Production Checklist

- Replace `SECRET_KEY` and OAuth credentials.
- Use managed PostgreSQL with PITR backups.
- Use Redis Cluster or managed Redis for lock durability.
- Use Kafka with replication factor 3.
- Enable HTTPS at the ingress.
- Store payment credentials in a cloud secret manager.
- Send payment card handling to a PCI-compliant gateway hosted page.
- Enable OpenTelemetry traces from gateway through AI and booking services.
- Configure Prometheus scrape targets and Grafana dashboards.

## Kubernetes

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/postgres.yaml
kubectl apply -f infra/k8s/redis.yaml
kubectl apply -f infra/k8s/backend.yaml
kubectl apply -f infra/k8s/frontend.yaml
```

