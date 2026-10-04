# Repositories and OCI registries

> Hands-on: [lab 11](../labs/11-repositories.md), the Traefik install in [lab 00](../labs/00-setup.md).

## 1 · What is it?

How charts are distributed. A **chart repository** is an HTTP server with an `index.yaml` and `.tgz` packages. An
**OCI registry** (GHCR, ECR, Docker Hub, Harbor...) stores charts as OCI artifacts, like container images.

## 2 · Why do repositories exist?

So that a chart is consumed by **name and version**, not by copying a folder: the publisher releases versions, users
pin and upgrade them.

## 3 · How do charts get distributed?

```text
 author:  helm package → .tgz → upload + index.yaml (HTTP repo)     or   helm push oci://registry/path
 user:    helm repo add + helm repo update → helm install repo/chart --version X
          helm install oci://registry/path/chart --version X     (no repo add needed)
```

## 4 · What problem does it solve?

Sharing charts across teams and organisations, with versions, and installing well-known software (ingress
controllers, monitoring, databases) from its maintainers.

## 5 · How do I use it?

Add only trusted repositories; `helm search repo`; read `helm show chart/values/readme` and render before installing;
always `--version`; keep your values in a file.

## 6 · What command should I run?

```bash
helm repo add podinfo https://stefanprodan.github.io/podinfo && helm repo update podinfo
helm search repo podinfo --versions
helm search hub podinfo                       # Artifact Hub
helm show values podinfo/podinfo --version 6.15.0
helm install catalog podinfo/podinfo --version 6.15.0 -f my-values.yaml
helm pull oci://ghcr.io/stefanprodan/charts/podinfo --version 6.15.0
helm registry login ghcr.io && helm push demo-app-1.0.0.tgz oci://ghcr.io/OWNER/charts
```

## 7 · What output should I expect?

`"podinfo" has been added to your repositories`; search tables with `CHART VERSION` and `APP VERSION`; `Pushed:` and
`Digest:` for OCI.

## 8 · What can go wrong?

`chart "x" matching 1.2.3 not found ... (try 'helm repo update')`: stale index or a version that does not exist;
`401/403` from a registry (login, or the artifact is private / does not exist); unpinned installs that change over time.

## 9 · How do I troubleshoot it?

`helm repo update`, `helm search repo NAME --versions`, `helm show chart REF --version X`; for OCI,
`helm registry login` and the registry's UI.

## 10 · Where is it used in real DevOps work?

Platform teams installing third-party infrastructure; companies publishing internal charts to a private OCI registry;
CI pushing a new chart version on every release ([this repository](../.github/workflows/test.yaml) pushes to GHCR).
