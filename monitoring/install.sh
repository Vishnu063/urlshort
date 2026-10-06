#!/usr/bin/env bash
set -e
export KUBECONFIG=~/.kube/urlshort.yaml
cd ~/urlshort

HOST=$(kubectl get ingress -n urlshort urlshort -o jsonpath='{.spec.rules[0].host}')
IP=${HOST#urlshort.}; IP=${IP%.nip.io}
echo "Server IP: $IP"

AVAIL=$(ssh -i ~/.ssh/urlshort -o StrictHostKeyChecking=no ubuntu@$IP 'free -m | grep Mem | tr -s " " | cut -d" " -f7')
echo "Available memory: ${AVAIL} MB"
if [ "$AVAIL" -lt 900 ]; then
  echo "Not enough free memory for monitoring. Move to the bigger server first."
  exit 1
fi

ssh -i ~/.ssh/urlshort ubuntu@$IP 'swapon --show | grep -q swapfile || {
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile &&
  sudo mkswap /swapfile && sudo swapon /swapfile &&
  echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab; }'

cat > monitoring/prometheus-values.yaml << CFG
alertmanager: { enabled: false }
prometheus-pushgateway: { enabled: false }
server:
  retention: 2d
  persistentVolume: { enabled: true, size: 2Gi }
  resources:
    requests: { cpu: 50m, memory: 200Mi }
    limits: { memory: 400Mi }
prometheus-node-exporter:
  resources:
    limits: { memory: 40Mi }
kube-state-metrics:
  resources:
    limits: { memory: 64Mi }
CFG

cat > monitoring/grafana-values.yaml << CFG
resources:
  requests: { cpu: 50m, memory: 100Mi }
  limits: { memory: 250Mi }
admin:
  existingSecret: grafana-admin
  userKey: admin-user
  passwordKey: admin-password
persistence: { enabled: false }
datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        url: http://prometheus-server.monitoring.svc
        isDefault: true
dashboardProviders:
  dashboardproviders.yaml:
    apiVersion: 1
    providers:
      - name: default
        folder: ""
        type: file
        options: { path: /var/lib/grafana/dashboards/default }
dashboards:
  default:
    node-exporter:
      gnetId: 1860
      revision: 37
      datasource: Prometheus
ingress:
  enabled: true
  ingressClassName: traefik
  hosts:
    - grafana.$IP.nip.io
CFG

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl -n monitoring get secret grafana-admin >/dev/null 2>&1 || \
  kubectl -n monitoring create secret generic grafana-admin \
    --from-literal=admin-user=admin \
    --from-literal=admin-password="$(openssl rand -base64 18)"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null
helm repo update >/dev/null

helm upgrade --install prometheus prometheus-community/prometheus -n monitoring -f monitoring/prometheus-values.yaml
helm upgrade --install grafana grafana/grafana -n monitoring -f monitoring/grafana-values.yaml

kubectl -n monitoring rollout status deploy/prometheus-server --timeout=300s
kubectl -n monitoring rollout status deploy/grafana --timeout=300s
kubectl get pods -n monitoring

echo
echo "Grafana:  http://grafana.$IP.nip.io"
echo "User:     admin"
echo -n "Password: "
kubectl -n monitoring get secret grafana-admin -o jsonpath="{.data.admin-password}" | base64 -d; echo
