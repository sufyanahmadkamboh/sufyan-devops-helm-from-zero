# Lab 07 · Install a release

> Level 9. Time: 35 minutes.

## Objective

Install demo-app as a release, inspect the release with every `helm get` command, find where Helm stores it, and
remove a release cleanly with `helm uninstall`.

## Prerequisites

- [Lab 06](06-rendering.md). The cluster with Traefik ([lab 00](00-setup.md)).

## Task

1. Install demo-app for the dev environment as release `demo` in namespace `demo-dev`.
2. Verify it from the Kubernetes side and from the Helm side.
3. Install a throwaway release, uninstall it, and check what is left.

## Commands

### 1 · Install

> A Helm installation creates a Helm release.

<!-- test: timeout=300; contains=STATUS: deployed; output -->
```bash
helm install demo charts/demo-app \
  --namespace demo-dev --create-namespace \
  -f charts/demo-app/values-dev.yaml \
  --wait --timeout 3m
```

```text
NAME: demo
LAST DEPLOYED: Sun Oct  4 23:30:20 2026
NAMESPACE: demo-dev
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
demo-app 1.0.0 (chart 1.0.0) is deployed as release "demo" in namespace "demo-dev".
Environment: dev · revision 1

Open:  http://demo-dev.localhost:8080/

Check it:
  kubectl --namespace demo-dev get pods -l app.kubernetes.io/instance=demo
  helm test demo --namespace demo-dev
```

| Part | Meaning |
|---|---|
| `demo` | the **release name**: unique within the namespace, part of every object's name |
| `charts/demo-app` | the chart: a folder here; also a `.tgz`, `repo/chart` or `oci://...` |
| `--namespace demo-dev --create-namespace` | where the objects and the release record go |
| `-f values-dev.yaml` | the environment's values on top of the chart's defaults |
| `--wait --timeout 3m` | wait until Deployments are ready (fail after 3 minutes); without it, Helm returns as soon as the objects are accepted |

### 2 · The Kubernetes side

<!-- test: contains=demo-demo-app; absent=0/1; output -->
```bash
kubectl get pods,svc,ingress --namespace demo-dev
```

```text
NAME                                 READY   STATUS    RESTARTS   AGE
pod/demo-demo-app-68d8b4d8dc-rlvzj   1/1     Running   0          1s

NAME                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/demo-demo-app   ClusterIP   10.96.213.161   <none>        8080/TCP   1s

NAME                                      CLASS     HOSTS                ADDRESS   PORTS   AGE
ingress.networking.k8s.io/demo-demo-app   traefik   demo-dev.localhost             80      1s
```

<!-- test: retry=20; contains=APP_ENV: "dev"; output -->
```bash
curl -s http://demo-dev.localhost:8080/config.js; echo
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };
```

Open <http://demo-dev.localhost:8080/> in a browser: the Bookshop frontend with `dev` in its footer (its APIs
are not deployed in this lab, so the panels report them unreachable: this chart is the frontend alone).

Every object carries the chart's labels: which app, which version, which release, which environment:

<!-- test: contains=dev; output -->
```bash
kubectl get pods --namespace demo-dev -L app.kubernetes.io/instance,app.kubernetes.io/version,environment
```

```text
NAME                             READY   STATUS    RESTARTS   AGE   INSTANCE   VERSION   ENVIRONMENT
demo-demo-app-68d8b4d8dc-rlvzj   1/1     Running   0          4s    demo       1.0.0     dev
```

### 3 · The Helm side

<!-- test: contains=deployed; output -->
```bash
helm list --namespace demo-dev
helm status demo --namespace demo-dev | head -7
```

```text
NAME	NAMESPACE	REVISION	UPDATED                               	STATUS  	CHART         	APP VERSION
demo	demo-dev 	1       	2026-10-04 23:30:20.3041473 +0200 CEST	deployed	demo-app-1.0.0	1.0.0      
NAME: demo
LAST DEPLOYED: Sun Oct  4 23:30:20 2026
NAMESPACE: demo-dev
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
RESOURCES:
```

`helm status` re-prints the summary and the NOTES at any time. What exactly did this release get?

| Command | Answers |
|---|---|
| `helm get values demo` | the values **you** supplied (here: the dev file) |
| `helm get values demo --all` | every value, defaults included |
| `helm get manifest demo` | the exact YAML Helm applied |
| `helm get notes demo` | the rendered NOTES.txt |
| `helm get hooks demo` | the hook resources (here: the test Pod) |
| `helm get metadata demo` | chart, versions, revision, status, dates |
| `helm get all demo` | all of the above together |

<!-- test: contains=demo-dev.localhost; output -->
```bash
helm get values demo --namespace demo-dev
```

```text
USER-SUPPLIED VALUES:
environment: dev
ingress:
  enabled: true
  hosts:
  - host: demo-dev.localhost
    paths:
    - path: /
      pathType: Prefix
replicaCount: 1
```

<!-- test: contains=kind: Deployment; output -->
```bash
helm get manifest demo --namespace demo-dev | grep -E '^(# Source|kind):'
```

```text
# Source: demo-app/templates/serviceaccount.yaml
kind: ServiceAccount
# Source: demo-app/templates/configmap.yaml
kind: ConfigMap
# Source: demo-app/templates/service.yaml
kind: Service
# Source: demo-app/templates/deployment.yaml
kind: Deployment
# Source: demo-app/templates/ingress.yaml
kind: Ingress
```

<!-- test: contains=REVISION: 1; output -->
```bash
helm get metadata demo --namespace demo-dev
```

```text
NAME: demo
CHART: demo-app
VERSION: 1.0.0
APP_VERSION: 1.0.0
ANNOTATIONS: 
LABELS: modifiedAt=1791149421,name=demo,owner=helm,status=deployed,version=1
DEPENDENCIES: 
NAMESPACE: demo-dev
REVISION: 1
STATUS: deployed
DEPLOYED_AT: 2026-10-04T23:30:20+02:00
APPLY_METHOD: server-side apply
```

### 4 · Where the release lives

<!-- test: contains=sh.helm.release.v1.demo.v1; output -->
```bash
kubectl get secrets --namespace demo-dev -l owner=helm --show-labels
```

```text
NAME                         TYPE                 DATA   AGE   LABELS
sh.helm.release.v1.demo.v1   helm.sh/release.v1   1      5s    modifiedAt=1791149421,name=demo,owner=helm,status=deployed,version=1
```

One Secret per **revision**, in the release's namespace, of type `helm.sh/release.v1`: it holds the chart, the values
and the rendered manifest of that revision (compressed). That is why `helm get manifest` works without the chart
folder, why anyone with access to the namespace sees the same releases, and why rollback (lab 09) can go back to any
revision Helm still keeps. Deleting these Secrets makes Helm forget the release (the objects stay, unmanaged): don't.

### 5 · Uninstall

A throwaway release in its own namespace:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install tmp charts/demo-app --namespace demo-tmp --create-namespace --wait --timeout 3m | grep STATUS
```

```text
⚠️ DESTRUCTIVE COMMAND · deletes every object of the release tmp.
```

<!-- test: timeout=300; contains=release "tmp" uninstalled; output -->
```bash
helm uninstall tmp --namespace demo-tmp --wait
```

```text
release "tmp" uninstalled
```

Verify: the release is gone from Helm, and its objects from Kubernetes:

<!-- test: retry=30; contains=No resources found; output -->
```bash
helm list --namespace demo-tmp
kubectl get all,configmap,secret,serviceaccount --namespace demo-tmp -l app.kubernetes.io/instance=tmp 2>&1
kubectl get namespace demo-tmp
```

```text
NAME	NAMESPACE	REVISION	UPDATED	STATUS	CHART	APP VERSION
No resources found in demo-tmp namespace.
NAME       STATUS   AGE
demo-tmp   Active   6s
```

Empty list, no objects with the release's label, and the release Secrets are gone too. (Run it right after the
uninstall and you may still see a Pod `Terminating`: Helm deleted the Deployment, and Kubernetes then stops its Pods
gracefully, which takes a few seconds.) But the **namespace** is still
there: `--create-namespace` created it, yet it is not part of the release. What `helm uninstall` removes and what it
leaves:

| Removed | Left behind |
|---|---|
| every object in the release's manifest | the namespace (not part of the release) |
| the release history (all revision Secrets) | PersistentVolumeClaims created by StatefulSets (`volumeClaimTemplates`) |
| | objects annotated `helm.sh/resource-policy: keep` |
| | hook resources (Jobs, test Pods) unless their delete policy removed them |
| | CRDs installed from a chart's `crds/` folder |

So after an uninstall, check the namespace, not just `helm list`. Remove it when nothing else lives there:

<!-- test: timeout=300 -->
```bash
kubectl delete namespace demo-tmp
```

## Expected Output

- `helm install`: `STATUS: deployed`, `REVISION: 1`, then the NOTES with `http://demo-dev.localhost:8080/`.
- `/config.js` contains `APP_ENV: "dev"`.
- One release Secret `sh.helm.release.v1.demo.v1`.

## Explanation

```text
helm install demo charts/demo-app -f values-dev.yaml
  │ 1 load chart + merge values
  │ 2 render templates → YAML
  │ 3 send objects to the API server
  │ 4 store revision 1 (Secret sh.helm.release.v1.demo.v1, status deployed)
  │ 5 --wait: watch until ready
  ▼
release "demo" (namespace demo-dev) ──► ServiceAccount, ConfigMap, Service, Deployment, Ingress
```

Helm manages the **release**; Kubernetes manages the **workloads**. Helm created a Deployment; the Deployment
controller created the ReplicaSet and Pods. If a Pod dies, Kubernetes replaces it: Helm is not involved.

## Break It

Run the same install again:

<!-- test: fail; contains=cannot reuse a name that is still in use; output -->
```bash
helm install demo charts/demo-app --namespace demo-dev -f charts/demo-app/values-dev.yaml
```

```text
level=ERROR msg="release name check failed" error="cannot reuse a name that is still in use"
Error: INSTALLATION FAILED: release name check failed: cannot reuse a name that is still in use
```

## Troubleshoot It

A release name is unique per namespace. `helm list -n demo-dev` shows `demo` already exists. Three different
intentions, three commands:

- Change the existing release → `helm upgrade demo ...` (lab 08).
- "Install if missing, otherwise upgrade" (CI pipelines) → `helm upgrade --install demo ...`, idempotent.
- A second, independent copy → another release name (the challenge).

<!-- test: timeout=300; contains=REVISION: 2 -->
```bash
helm upgrade --install demo charts/demo-app --namespace demo-dev -f charts/demo-app/values-dev.yaml --wait | grep REVISION
```

Nothing in the chart or values changed, yet it is revision 2: every upgrade is recorded, even a no-op.

## Challenge

Install a second, independent copy of demo-app in the **same** namespace, release `blue`, reachable at
`http://demo-blue.localhost:8080/`, with environment `blue`. Both releases must keep working.

## Solution

<details>
<summary>Open the solution</summary>

Values with lists (`ingress.hosts`) are easiest in a small file:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
mkdir -p labs/work
cat > labs/work/blue.yaml <<'EOF'
environment: blue
ingress:
  enabled: true
  hosts:
    - host: demo-blue.localhost
      paths:
        - path: /
          pathType: Prefix
EOF
helm install blue charts/demo-app --namespace demo-dev -f labs/work/blue.yaml --wait | grep STATUS
```

</details>

## Verification

<!-- test: retry=20; contains=APP_ENV: "blue"; contains=APP_ENV: "dev"; output -->
```bash
curl -s http://demo-blue.localhost:8080/config.js; echo
curl -s http://demo-dev.localhost:8080/config.js; echo
helm list --namespace demo-dev
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "blue" };

window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

NAME	NAMESPACE	REVISION	UPDATED                               	STATUS  	CHART         	APP VERSION
blue	demo-dev 	1       	2026-10-04 23:30:38.0954753 +0200 CEST	deployed	demo-app-1.0.0	1.0.0      
demo	demo-dev 	2       	2026-10-04 23:30:37.5118824 +0200 CEST	deployed	demo-app-1.0.0	1.0.0      
```

Two releases of one chart, in one namespace: the release name keeps their objects (`blue-demo-app`,
`demo-demo-app`) and labels apart.

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls the release blue.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall blue --namespace demo-dev --wait
rm -f labs/work/blue.yaml
```

Keep the release `demo`: labs 08 and 09 upgrade and roll it back.

Next: [lab 08 · Upgrade](08-upgrade.md).
