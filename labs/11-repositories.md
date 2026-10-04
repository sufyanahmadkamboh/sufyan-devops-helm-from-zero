# Lab 11 · Repositories and existing charts

> Level 13. Time: 40 minutes. Needs internet access (public chart repositories) and Docker (a local registry).

## Objective

Use Helm the way most engineers use it most of the time: find a chart someone else maintains, review it, install it
with your own values, upgrade it. Then publish a chart of your own to a registry.

## Prerequisites

- [Lab 10](10-environments.md).

## Task

1. Add the [podinfo](https://github.com/stefanprodan/podinfo) chart repository (a small, well-maintained demo
   application from a maintainer of the Flux project, used in many Kubernetes tutorials).
2. Search it, review the chart, install a pinned version with a values file.
3. Pull the same chart from an OCI registry.
4. Publish demo-app to a local OCI registry and install it from there.

## Commands

### 1 · What a repository is

A **chart repository** is a web server with an `index.yaml` (every chart, every version, where to download it) and
the packaged `.tgz` files. Nothing more:

<!-- test: contains=apiVersion: v1; output=head:14 -->
```bash
curl -s https://stefanprodan.github.io/podinfo/index.yaml | grep -v email | head -13
```

```text
apiVersion: v1
entries:
  podinfo:
  - apiVersion: v1
    appVersion: 6.15.0
    created: "2026-08-31T15:40:34.904896083Z"
    description: Podinfo Helm chart for Kubernetes
    digest: 5ca7896889b539e04cdad4df2093ff1ff7576295e7e3ef90a1e1845e3a334d75
    home: https://github.com/stefanprodan/podinfo
    kubeVersion: '>=1.23.0-0'
    maintainers:
      name: stefanprodan
    name: podinfo
```

An **OCI registry** (the same kind of registry that stores container images: GHCR, Docker Hub, ECR, Harbor) can store
charts too, without an index. Helm supports both; OCI is where the ecosystem is moving.

```text
 chart author ── helm package ──► demo-app-1.0.0.tgz ──┬── upload + index.yaml   (HTTP repository)
                                                       └── helm push oci://...   (OCI registry)
 chart user   ── helm repo add / helm install repo/chart --version X
              ── helm install oci://registry/path/chart --version X
```

### 2 · Add, update, list, search

You already have one repository from [lab 00](00-setup.md):

<!-- test: contains=traefik; output -->
```bash
helm repo list
```

```text
NAME   	URL                                   
traefik	https://traefik.github.io/charts      
podinfo	https://stefanprodan.github.io/podinfo
```

<!-- test: timeout=120; contains=podinfo; output -->
```bash
helm repo add podinfo https://stefanprodan.github.io/podinfo
helm repo update podinfo
```

```text
"podinfo" already exists with the same configuration, skipping
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "podinfo" chart repository
Update Complete. ⎈Happy Helming!⎈
```

`repo add` gives the URL a local name; `repo update` downloads its current `index.yaml` into Helm's cache.
Searching only reads that cached index, so it is fast, and stale until you update.

<!-- test: contains=podinfo/podinfo; output -->
```bash
helm search repo podinfo
helm search repo podinfo --versions | head -5
```

```text
NAME           	CHART VERSION	APP VERSION	DESCRIPTION                      
podinfo/podinfo	6.15.0       	6.15.0     	Podinfo Helm chart for Kubernetes
NAME           	CHART VERSION	APP VERSION	DESCRIPTION                      
podinfo/podinfo	6.15.0       	6.15.0     	Podinfo Helm chart for Kubernetes
podinfo/podinfo	6.14.1       	6.14.1     	Podinfo Helm chart for Kubernetes
podinfo/podinfo	6.14.0       	6.14.0     	Podinfo Helm chart for Kubernetes
podinfo/podinfo	6.13.0       	6.13.0     	Podinfo Helm chart for Kubernetes
```

To discover charts you have not added yet, `helm search hub` queries [Artifact Hub](https://artifacthub.io), the
public catalogue of charts:

<!-- test: timeout=120; contains=artifacthub.io; output=head:4 -->
```bash
helm search hub podinfo --max-col-width 60
```

```text
URL                                                 	CHART VERSION	APP VERSION	DESCRIPTION                               
https://artifacthub.io/packages/helm/podinfo/podinfo	6.15.0       	6.15.0     	Podinfo Helm chart for Kubernetes         
https://artifacthub.io/packages/helm/flagger/podinfo	6.1.4        	6.1.3      	Flagger canary deployment demo application
```

Artifact Hub lists charts from thousands of publishers; listing is not an endorsement. Check who publishes a chart,
whether it is maintained, and what it does before trusting it ([security](../docs/13-security.md)).

### 3 · Review before you install

You are about to run someone else's YAML in your cluster. Read its interface first:

<!-- test: contains=appVersion: 6.14.1; output -->
```bash
helm show chart podinfo/podinfo --version 6.14.1 | grep -v email
```

```text
apiVersion: v1
appVersion: 6.14.1
description: Podinfo Helm chart for Kubernetes
home: https://github.com/stefanprodan/podinfo
kubeVersion: '>=1.23.0-0'
maintainers:
  name: stefanprodan
name: podinfo
sources:
- https://github.com/stefanprodan/podinfo
version: 6.14.1
```

<!-- test: contains=message; output -->
```bash
helm show values podinfo/podinfo --version 6.14.1 | grep -A4 -E '^(replicaCount|image|ui):'
```

```text
replicaCount: 1
logLevel: info
host: #0.0.0.0
backend: #http://backend-podinfo:9898/echo
backends: []
--
image:
  repository: ghcr.io/stefanprodan/podinfo
  tag: 6.14.1
  pullPolicy: IfNotPresent
  pullSecrets: []
--
ui:
  color: "#34577c"
  message: ""
  logo: ""
```

And what it would actually create, with the image it would run:

<!-- test: contains=ghcr.io/stefanprodan/podinfo:6.14.1; output -->
```bash
helm template catalog podinfo/podinfo --version 6.14.1 | grep -E '^kind:|image:' | sort | uniq -c
```

```text
      1           image: "ghcr.io/stefanprodan/podinfo:6.14.1"
      1       image: curlimages/curl:7.69.0
      1       image: giantswarm/tiny-tools
      1       image: stefanprodan/grpc_health_probe:v0.3.0
      1 kind: Deployment
      3 kind: Pod
      1 kind: Service
```

A Deployment and a Service running the application image from the maintainer's own registry, nothing cluster-wide,
no RBAC. But also three test Pods (`helm test`) with three more images from Docker Hub, two of them with old tags
(`curl:7.69.0`) or no tag at all (`tiny-tools`). They only run during `helm test`, yet they are images you would
pull into your cluster: exactly the kind of detail a review is for. Your organisation may require mirroring or
replacing such images, or simply not running that chart's tests.

### 4 · Install with your values

Values go in a file, reviewed and kept in Git, not in a long `--set` line:

<!-- test: contains=podinfo.localhost -->
```bash
mkdir -p labs/work
cat > labs/work/podinfo-values.yaml <<'EOF'
# Our settings for the podinfo chart (keys from: helm show values podinfo/podinfo)
replicaCount: 2
ui:
  message: "Bookshop catalog, installed from a public chart"
  color: "#1f6f50"
ingress:
  enabled: true
  className: traefik
  hosts:
    - host: podinfo.localhost
      paths:
        - path: /
          pathType: Prefix
resources:
  requests: { cpu: 10m, memory: 32Mi }
  limits: { memory: 64Mi }
EOF
grep host: labs/work/podinfo-values.yaml
```

Always pin `--version`: without it you get whatever is newest today, and a different chart tomorrow.

<!-- test: timeout=300; contains=STATUS: deployed; output=head:6 -->
```bash
helm install catalog podinfo/podinfo --version 6.14.1 \
  --namespace lab-11 --create-namespace \
  -f labs/work/podinfo-values.yaml --wait --timeout 3m
```

```text
NAME: catalog
LAST DEPLOYED: Sun Oct  4 23:42:41 2026
NAMESPACE: lab-11
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
...
```

<!-- test: retry=20; contains=Bookshop catalog; output -->
```bash
curl -s http://podinfo.localhost:8080/ | grep -E '"(hostname|version|message)"'
```

```text
  "hostname": "catalog-podinfo-7756f557ff-68txd",
  "version": "6.14.1",
  "message": "Bookshop catalog, installed from a public chart",
```

Open <http://podinfo.localhost:8080/> in a browser too: podinfo's UI shows the message in our colour.

### 5 · The same chart from an OCI registry

The podinfo maintainer also publishes the chart to GHCR. No `repo add`: the reference is the address:

<!-- test: timeout=120; contains=version: 6.14.1; output=tail:4 -->
```bash
helm show chart oci://ghcr.io/stefanprodan/charts/podinfo --version 6.14.1 2>&1 | grep -E '^(Pulled|Digest|name|version)'
```

```text
Pulled: ghcr.io/stefanprodan/charts/podinfo:6.14.1
Digest: sha256:6432072d76519fd808e4fb6eb892f9cbcbb1a79c161ac02dbf6ad445c931616b
name: podinfo
version: 6.14.1
```

The **digest** identifies the exact content. Pinning `--version` trusts the publisher not to re-push a version;
pinning the digest (`oci://...podinfo@sha256:...`) trusts nobody.

### 6 · Publish your own chart

Teams publish their charts so others can install a version instead of copying a folder. A local OCI registry (the
open-source `registry` image) stands in for GHCR or ECR. This repository's CI pushes `demo-app` and `bookshop` to
GHCR the same way ([test.yaml](../.github/workflows/test.yaml)).

<!-- test-run: docker rm -f helm-registry > /dev/null 2>&1 || true -->

<!-- test: timeout=300; contains=Pushed: localhost:5001/charts/demo-app:1.0.0; output -->
```bash
docker pull -q registry:3 > /dev/null
docker run -d --name helm-registry -p 127.0.0.1:5001:5000 registry:3 > /dev/null
sleep 2
helm package charts/demo-app --destination labs/work > /dev/null
helm push labs/work/demo-app-1.0.0.tgz oci://localhost:5001/charts --plain-http
```

```text
Pushed: localhost:5001/charts/demo-app:1.0.0
Digest: sha256:4b88bdb2ba1d3cf0b8c0c7b987152c7b7b56246cb1d2f4f4d46bd3fd7b44da09
```

(`--plain-http` because this local registry has no TLS; never for a real registry.) Anyone with access can now
install it by reference:

<!-- test: timeout=300; contains=STATUS: deployed; output=head:7 -->
```bash
helm install shopfront oci://localhost:5001/charts/demo-app --version 1.0.0 --plain-http \
  --namespace lab-11 --wait --timeout 3m
```

```text
Pulled: localhost:5001/charts/demo-app:1.0.0
Digest: sha256:4b88bdb2ba1d3cf0b8c0c7b987152c7b7b56246cb1d2f4f4d46bd3fd7b44da09
NAME: shopfront
LAST DEPLOYED: Sun Oct  4 23:43:00 2026
NAMESPACE: lab-11
STATUS: deployed
REVISION: 1
...
```

## Expected Output

- `helm search repo podinfo`: chart `podinfo/podinfo`, chart version and app version `6.15.0` (the newest at the
  time of writing).
- The podinfo API answers with `"message": "Bookshop catalog, installed from a public chart"` and version `6.14.1`.
- `Pushed: localhost:5001/charts/demo-app:1.0.0`, then a release `shopfront` from that registry.

## Explanation

| You want to | Command |
|---|---|
| Register an HTTP repository | `helm repo add NAME URL` |
| Refresh the index | `helm repo update [NAME]` |
| Find a chart | `helm search repo WORD` (added repos), `helm search hub WORD` (Artifact Hub) |
| Read a chart | `helm show chart\|values\|readme\|all REF --version X` |
| Download it | `helm pull REF --version X [--untar]` |
| Publish to OCI | `helm package DIR` then `helm push FILE.tgz oci://HOST/PATH` (after `helm registry login`) |

Where would you use this at work? Installing platform components (ingress controllers, cert-manager, monitoring
stacks) from their maintainers' charts, and sharing your team's charts across teams through an internal OCI
registry, with versions instead of copies.

## Break It

<!-- test: fail; contains=not found; output -->
```bash
helm upgrade catalog podinfo/podinfo --version 6.99.0 --namespace lab-11 -f labs/work/podinfo-values.yaml
```

```text
Error: chart "podinfo" matching 6.99.0 not found in podinfo index. (try 'helm repo update'): no chart version found for podinfo-6.99.0
```

## Troubleshoot It

The message names the version and the repository's index. Either the version does not exist, or your cached index
is older than the release you are looking for. Check what the index knows, then refresh it:

<!-- test: timeout=120; contains=6.15.0; output -->
```bash
helm repo update podinfo > /dev/null
helm search repo podinfo/podinfo --versions | head -4
```

```text
NAME           	CHART VERSION	APP VERSION	DESCRIPTION                      
podinfo/podinfo	6.15.0       	6.15.0     	Podinfo Helm chart for Kubernetes
podinfo/podinfo	6.14.1       	6.14.1     	Podinfo Helm chart for Kubernetes
podinfo/podinfo	6.14.0       	6.14.0     	Podinfo Helm chart for Kubernetes
```

6.99.0 does not exist. (When a version you know was just released is missing, `helm repo update` is the fix.)

## Challenge

Upgrade the `catalog` release from chart 6.14.1 to **6.15.0** with the same values. Before upgrading, check what the
new chart version changes in the rendered manifests. Afterwards, prove the new application version is running.

## Solution

<details>
<summary>Open the solution</summary>

Compare the two renders with the same values (the version change of the image is expected; anything else is a
change the chart's maintainers made):

<!-- test: contains=6.15.0; output -->
```bash
diff <(helm template catalog podinfo/podinfo --version 6.14.1 -f labs/work/podinfo-values.yaml --namespace lab-11) \
     <(helm template catalog podinfo/podinfo --version 6.15.0 -f labs/work/podinfo-values.yaml --namespace lab-11) \
  | grep -E '^[<>]' | head -12 || true
```

```text
<     helm.sh/chart: podinfo-6.14.1
>     helm.sh/chart: podinfo-6.15.0
<     app.kubernetes.io/version: "6.14.1"
>     app.kubernetes.io/version: "6.15.0"
<     helm.sh/chart: podinfo-6.14.1
>     helm.sh/chart: podinfo-6.15.0
<     app.kubernetes.io/version: "6.14.1"
>     app.kubernetes.io/version: "6.15.0"
<           image: "ghcr.io/stefanprodan/podinfo:6.14.1"
>           image: "ghcr.io/stefanprodan/podinfo:6.15.0"
<     helm.sh/chart: podinfo-6.14.1
>     helm.sh/chart: podinfo-6.15.0
```

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade catalog podinfo/podinfo --version 6.15.0 --namespace lab-11 \
  -f labs/work/podinfo-values.yaml --wait --timeout 3m | grep STATUS
```

Upgrading a third-party chart is two upgrades in one: the chart (templates, defaults) and the application. Read the
chart's release notes for both.

</details>

## Verification

<!-- test: retry=20; contains="version": "6.15.0"; contains=podinfo-6.15.0; output -->
```bash
helm list --namespace lab-11
curl -s http://podinfo.localhost:8080/ | grep '"version"'
```

```text
NAME     	NAMESPACE	REVISION	UPDATED                               	STATUS  	CHART         	APP VERSION
catalog  	lab-11   	2       	2026-10-04 23:43:01.9692972 +0200 CEST	deployed	podinfo-6.15.0	6.15.0     
shopfront	lab-11   	1       	2026-10-04 23:43:00.13753 +0200 CEST  	deployed	demo-app-1.0.0	1.0.0      
  "version": "6.15.0",
```

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls catalog and shopfront, deletes the namespace lab-11, stops the local registry.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall catalog shopfront --namespace lab-11 --wait
kubectl delete namespace lab-11 --wait=false > /dev/null
docker rm -f helm-registry > /dev/null
rm -f labs/work/podinfo-values.yaml labs/work/demo-app-1.0.0.tgz
```

The `podinfo` repository entry stays: [lab 12](12-dependencies.md) uses it. Remove a repository with
`helm repo remove NAME`.

Next: [lab 12 · Dependencies](12-dependencies.md).
