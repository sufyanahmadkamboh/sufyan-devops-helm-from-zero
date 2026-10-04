#!/usr/bin/env bash
# First look at a Helm release that misbehaves: the Helm side, then the Kubernetes side, in one screen.
#   troubleshooting/triage.sh RELEASE NAMESPACE
# Read-only: it changes nothing.
set -u

release="${1:?usage: triage.sh RELEASE NAMESPACE}"
ns="${2:?usage: triage.sh RELEASE NAMESPACE}"
selector="app.kubernetes.io/instance=${release}"

section() { printf '\n== %s\n' "$1"; }

section "helm status"
helm status "$release" --namespace "$ns" 2>&1 | grep -E '^(NAME|STATUS|REVISION|DESCRIPTION|LAST DEPLOYED):'

section "helm history (last 3)"
helm history "$release" --namespace "$ns" --max 3 2>&1 | cut -c1-140

section "values supplied by the user"
helm get values "$release" --namespace "$ns" 2>&1

section "pods"
kubectl get pods --namespace "$ns" -l "$selector" -o wide 2>&1 | cut -c1-140

section "workloads and services"
kubectl get deployments,statefulsets,services,ingresses --namespace "$ns" -l "$selector" 2>&1

section "service endpoints"
kubectl get endpointslices --namespace "$ns" \
  -o custom-columns='SERVICE:.metadata.labels.kubernetes\.io/service-name,ENDPOINTS:.endpoints[*].addresses[0]' 2>&1

section "warning events (last 8)"
kubectl get events --namespace "$ns" --field-selector type=Warning --sort-by=.lastTimestamp \
  -o custom-columns='OBJECT:.involvedObject.name,REASON:.reason,MESSAGE:.message' 2>&1 | tail -8 | cut -c1-160
