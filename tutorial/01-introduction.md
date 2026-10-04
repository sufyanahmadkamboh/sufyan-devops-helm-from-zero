# Chapter 01 · Introduction

> Lesson: [lab 00 · Setup](../labs/00-setup.md). Time: 30 minutes.

## What this course is

By the end you will deploy a five-service application with a database to three environments from one chart, upgrade
it, break it, roll it back, test it, and explain every line of the chart. More importantly, you will have a method:
render before you apply, compare what Helm applied with what runs, change things only through Helm.

We start with something you already know (Kubernetes YAML) and only then introduce Helm, because a tool makes sense
only once you have felt the problem it solves.

## Tour the repository

```text
environments/   the problem: the Bookshop as raw YAML, three times
charts/         the solution: demo-app (lessons), bookshop (production-style), postgres (a dependency)
examples/       small charts, one idea each
labs/           the hands-on path, 00–16
troubleshooting/  12 broken deployments
docs/           concepts, security, best practices, cheat sheet
```

## Do

Run [lab 00](../labs/00-setup.md): create the kind cluster and install Traefik.

## Watch for

```text
NAME                     STATUS   ROLES           AGE   VERSION
helm-lab-control-plane   Ready    control-plane   ...   v1.37.0
helm-lab-worker          Ready    <none>          ...   v1.37.0
```

Two Docker containers acting as Kubernetes nodes. Then Traefik's answer to a request for a host nobody serves yet:

```text
404 page not found
```

That 404 is good news: your request reached the ingress controller through `localhost:8080` and NodePort 30080.

## Think like an engineer

You just ran `helm install traefik traefik/traefik --version 41.6.1 --values ...`: one command installed a
Deployment, a Service, RBAC rules and an IngressClass, configured by a 15-line values file. Keep that command in mind.
By chapter 16 you will be able to read every word of it, and to review what it installed before trusting it.

## Checkpoint

- [ ] `kubectl get nodes` shows two `Ready` nodes.
- [ ] `curl -s http://anything.localhost:8080/` prints `404 page not found`.
- [ ] You can say what kind does and why `*.localhost` works without editing `/etc/hosts`.

Next: [02 · The Kubernetes YAML problem](02-the-yaml-problem.md).
