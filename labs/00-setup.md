# Lab 00 · The lab cluster

> Before Level 1. Time: 10 minutes. You need Docker, [kind](https://kind.sigs.k8s.io/) v0.33, kubectl v1.37 and
> Helm v4.3 (how to install each: [README](../README.md#prerequisites); Helm in detail: [lab 01](01-install-helm.md)).

Every lesson runs on a local Kubernetes cluster: **kind** ("Kubernetes in Docker") runs each node as a Docker
container. It is a real Kubernetes 1.37, the same API and the same kubectl as a cloud cluster.

```text
 your computer
 ├── Docker
 │    ├── container helm-lab-control-plane   (control plane + node)
 │    └── container helm-lab-worker          (a worker node: the Pods run here)
 └── http://<name>.localhost:8080 ──► node port 30080 ──► Traefik (ingress controller) ──► the right Service
```

## Step 1 · Create the cluster

[kubernetes/cluster/kind-config.yaml](../kubernetes/cluster/kind-config.yaml) describes it: two nodes, Kubernetes 1.37.0
(node image pinned by digest), and port 30080 of the nodes published on your computer as `localhost:8080`.

<!-- test-run: kind delete cluster --name helm-lab > /dev/null 2>&1 || true -->

<!-- test: timeout=600; contains=kind-helm-lab; output=tail:3 -->
```bash
kind create cluster --config kubernetes/cluster/kind-config.yaml 2>&1
```

```text
...
kubectl cluster-info --context kind-helm-lab

Have a question, bug, or feature request? Let us know! https://kind.sigs.k8s.io/#community 🙂
```

<!-- test: retry=30; contains=helm-lab-worker; absent=NotReady; output -->
```bash
kubectl config current-context
kubectl get nodes
```

```text
kind-helm-lab
NAME                     STATUS   ROLES           AGE   VERSION
helm-lab-control-plane   Ready    control-plane   26s   v1.37.0
helm-lab-worker          Ready    <none>          15s   v1.37.0
```

## Step 2 · An ingress controller

The lessons reach applications through **Ingress** rules (`demo-dev.localhost` → the demo Service). Rules need an
ingress controller that reads them and routes the traffic: Traefik. We install it with one Helm command, using
someone else's chart as a black box. By [lab 11](11-repositories.md) you will understand every part of this
command; for now, notice that one command installs a complete, configured piece of infrastructure.

<!-- test: timeout=600; contains=deployed; output=tail:3 -->
```bash
helm repo add traefik https://traefik.github.io/charts > /dev/null 2>&1 || true
helm repo update traefik > /dev/null
helm install traefik traefik/traefik --version 41.6.1 --namespace traefik --create-namespace \
  --values kubernetes/cluster/traefik-values.yaml --wait --timeout 5m
```

```text
...
TEST SUITE: None
NOTES:
traefik with docker.io/traefik:v3.7.13 has been deployed successfully on traefik namespace!
```

The settings it used are in [kubernetes/cluster/traefik-values.yaml](../kubernetes/cluster/traefik-values.yaml): a
NodePort service on 30080 and the IngressClass `traefik`.

<!-- test: retry=15; contains=404 page not found; output -->
```bash
curl -s http://anything.localhost:8080/
```

```text
404 page not found
```

Traefik answers `404 page not found`: requests reach it, and nothing is deployed yet. (`*.localhost` names point to
your own computer; curl and browsers resolve them without any setup.)

The cluster is ready. Next, Level 1: [the problem Helm solves](../environments/README.md).
