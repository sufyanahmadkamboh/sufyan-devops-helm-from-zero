# Lab 16 · Capstone: from raw YAML to a Helm-managed platform

> Level 20. Time: 2–4 hours if you build the chart yourself, 45 minutes with the reference chart.

## Objective

Take the multi-stack Bookshop from plain Kubernetes YAML to a Helm chart, and operate it through a full release
lifecycle: install, verify, upgrade, a failed upgrade, troubleshooting, rollback, tests, history, cleanup.

```text
 environments/staging/*.yaml ──(1–2)──► your chart ──(3–8)──► lint, render ──(9–10)──► release "shop"
                                                                                          │
           cleanup (19) ◄── history (18) ◄── test (17) ◄── rollback (16) ◄── break (14–15) ◄── upgrade (13)
```

## Prerequisites

- Every lab so far, the [troubleshooting scenarios](../troubleshooting/README.md), and
  [Level 19](../docs/16-production-style-chart.md).
- The cluster with Traefik. The `shop` release in `bookshop-dev` may still be running; the capstone works in
  `bookshop-staging`.

## Task

Build a chart for the Bookshop (five services and PostgreSQL) that meets these requirements, then run the 19-step
workflow below with it.

| Requirement | Reference |
|---|---|
| Deployment, Service per service; one ConfigMap; one Secret; Ingress | lab 05 |
| Persistent storage for the database | dependency, lab 12 |
| Resource requests/limits, liveness/readiness (and startup) probes | lab 03 |
| Consistent labels from helpers (app, version, environment, release) | lab 14 |
| `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml` with only the differences | lab 10 |
| A chart version and an application version | lab 03 |
| `NOTES.txt` and a Helm test | lab 14 |
| No password in any values file | Level 17 |

[charts/bookshop](../charts/bookshop) is the **reference solution**. Build your own in `labs/work/` first if you want
the full exercise; the commands below use the reference chart (replace `charts/bookshop` with your folder).

## Commands

### 1 · Deploy manually using Kubernetes YAML

<!-- test-run: kubectl wait --for=delete namespace/bookshop-staging --timeout=300s > /dev/null 2>&1 || true -->

<!-- test: timeout=600; contains=successfully rolled out -->
```bash
kubectl apply -f environments/staging/namespace.yaml > /dev/null
kubectl apply -f environments/staging/ > /dev/null
for d in frontend node-api java-api python-api go-status; do
  kubectl -n bookshop-staging rollout status deployment/$d --timeout=300s
done
```

<!-- test: retry=20; contains=APP_ENV: "staging"; output -->
```bash
curl -s http://staging.bookshop.localhost:8080/config.js; echo
kubectl get deployments --namespace bookshop-staging
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "staging" };

NAME         READY   UP-TO-DATE   AVAILABLE   AGE
frontend     2/2     2            2           26s
go-status    2/2     2            2           26s
java-api     2/2     2            2           26s
node-api     2/2     2            2           26s
python-api   2/2     2            2           26s
```

### 2 · Identify configuration duplication

<!-- test: contains=bookshop-node-api; output -->
```bash
echo "lines per environment: $(cat environments/staging/*.yaml | wc -l)"
echo "lines that differ from dev: $(diff -r environments/dev environments/staging | grep -c '^[<>]')"
grep -rn 'image:' environments/staging/deployments.yaml | sed 's/ *#.*//'
```

```text
lines per environment: 458
lines that differ from dev: 74
22:          image: ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0
79:          image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
130:          image: ghcr.io/sufyanahmadkamboh/bookshop-python-api:1.0.0
181:          image: ghcr.io/sufyanahmadkamboh/bookshop-go-status:1.0.0
224:          image: ghcr.io/sufyanahmadkamboh/bookshop-java-api:1.0.0
```

Write down what differs (namespace, replicas, `APP_ENV`, host, volume size, password) and what repeats (everything
else). That list is your values design. Remove the manual deployment before Helm takes over the same names and host:

```text
⚠️ DESTRUCTIVE COMMAND · deletes the namespace bookshop-staging and everything in it.
```

<!-- test: timeout=300; contains=deleted -->
```bash
kubectl delete namespace bookshop-staging
```

### 3 · Create a Helm chart

<!-- test-run: rm -rf labs/work/capstone -->

<!-- test: contains=Creating -->
```bash
mkdir -p labs/work/capstone
helm create labs/work/capstone/bookshop
```

Your starting point. Keep `_helpers.tpl`, `NOTES.txt`, `tests/`; replace the single Deployment with one template that
ranges over the services.

### 4 · Convert YAML into templates · 5 · Move configuration into values

Compare one service, raw against rendered, to check your conversion keeps what matters:

<!-- test: contains=bookshop-node-api:1.0.0; output -->
```bash
echo "--- raw (environments/staging)"
sed -n '/name: node-api$/,/^---/p' environments/staging/deployments.yaml | grep -E 'replicas:|image:|containerPort:|path:' | sed 's/ *#.*//'
echo "--- chart (charts/bookshop, staging values)"
helm template shop charts/bookshop -f charts/bookshop/values-staging.yaml --show-only templates/services.yaml \
  | sed -n '/name: shop-node-api$/,/^---/p' | grep -E 'replicas:|image:|containerPort:|path:'
```

```text
--- raw (environments/staging)
  replicas: 2
          image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
              containerPort: 3000
            httpGet: { path: /health, port: http }
            httpGet: { path: /ready, port: http }
--- chart (charts/bookshop, staging values)
  replicas: 2
          image: "ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0"
              containerPort: 3000
            httpGet: { path: /health, port: http }
            httpGet: { path: /ready, port: http }
```

Same image, same port, same probes, same replica count, now from values.

### 6–8 · Values per environment

<!-- test: contains=environment: prod; output -->
```bash
for env in dev staging prod; do echo "# values-$env.yaml"; grep -v '^#' charts/bookshop/values-$env.yaml; done
```

```text
# values-dev.yaml
environment: dev
ingress:
  host: dev.bookshop.localhost
# values-staging.yaml
environment: staging
services:
  node-api: { replicas: 2 }
  python-api: { replicas: 2 }
postgres:
  persistence:
    size: 2Gi
ingress:
  host: staging.bookshop.localhost
# values-prod.yaml
environment: prod
services:
  frontend:
    image: { tag: "1.0.0" }
    replicas: 2
  node-api:
    image: { tag: "1.0.0" }
    resources:
      requests: { cpu: 100m, memory: 128Mi }
      limits: { cpu: "1", memory: 512Mi }
  python-api:
    image: { tag: "1.0.0" }
    replicas: 2
  go-status:
    image: { tag: "1.0.0" }
    replicas: 2
  java-api:
    image: { tag: "1.0.0" }
    replicas: 2
report:
  image: { tag: "1.0.0" }
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 6
podDisruptionBudget:
  enabled: true
postgres:
  persistence:
    size: 5Gi
ingress:
  host: bookshop.localhost
```

### 9 · Lint the chart · 10 · Render it

<!-- test: timeout=120; contains=0 chart(s) failed; absent=ERROR; output -->
```bash
helm dependency build charts/bookshop > /dev/null
for env in dev staging prod; do
  helm lint charts/bookshop -f charts/bookshop/values-$env.yaml --quiet && echo "$env: lint ok"
  helm template shop charts/bookshop -f charts/bookshop/values-$env.yaml | grep -c '^kind:' | sed "s/^/$env: objects rendered: /"
done
helm lint charts/bookshop -f charts/bookshop/values-staging.yaml | tail -1
```

```text
dev: lint ok
dev: objects rendered: 17
staging: lint ok
staging: objects rendered: 17
prod: lint ok
prod: objects rendered: 23
1 chart(s) linted, 0 chart(s) failed
```

### 11 · Install the release

<!-- test: timeout=900; contains=STATUS: deployed; output=head:14 -->
```bash
helm upgrade --install shop charts/bookshop --namespace bookshop-staging --create-namespace \
  -f charts/bookshop/values-staging.yaml --wait --timeout 10m
```

```text
Release "shop" does not exist. Installing it now.
NAME: shop
LAST DEPLOYED: Mon Oct  5 00:35:13 2026
NAMESPACE: bookshop-staging
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
Bookshop 1.0.0 (chart 1.2.0) · release "shop" · namespace "bookshop-staging" · environment staging · revision 1

Services:
  frontend    ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0 × 1
  go-status   ghcr.io/sufyanahmadkamboh/bookshop-go-status:1.0.0 × 1
  java-api    ghcr.io/sufyanahmadkamboh/bookshop-java-api:1.0.0 × 1
...
```

### 12 · Verify the application

<!-- test: retry=20; contains=Ada Lovelace; contains=APP_ENV: "staging"; output -->
```bash
kubectl get pods --namespace bookshop-staging
curl -s http://staging.bookshop.localhost:8080/config.js; echo
curl -s http://staging.bookshop.localhost:8080/api/users | head -c 100; echo
kubectl logs --namespace bookshop-staging job/shop-report | tail -1
```

```text
NAME                               READY   STATUS      RESTARTS   AGE
shop-frontend-5c9fb4cb45-ss82j     1/1     Running     0          27s
shop-go-status-59cc574b9d-qrqx9    1/1     Running     0          27s
shop-java-api-f7bcdfdd7-9ffn5      1/1     Running     0          27s
shop-node-api-64f4cb4bcf-d4h9w     1/1     Running     0          27s
shop-node-api-64f4cb4bcf-ms4j6     1/1     Running     0          27s
shop-postgres-0                    1/1     Running     0          27s
shop-python-api-5b48d98bf9-h2gxw   1/1     Running     0          27s
shop-python-api-5b48d98bf9-kd8vt   1/1     Running     0          27s
shop-report-4dbvs                  0/1     Completed   0          4s
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "staging" };

[{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-10-04T22:35:29.145Z"},{"
2026-10-04T22:35:37.976Z report-worker report #1 saved: users=3 books=5 reviews=0 services up=5/5
```

### 13 · Upgrade the application

The node-api team released **1.1.0**. Promote it to staging with a small overlay file, so the change is reviewable
and repeatable (not a `--set` lost in a shell history):

<!-- test: contains=1.1.0 -->
```bash
cat > labs/work/capstone/node-api-1.1.0.yaml <<'EOF'
# Release overlay: node-api 1.1.0 (applied on top of the environment's values file)
services:
  node-api:
    image: { tag: "1.1.0" }
EOF
cat labs/work/capstone/node-api-1.1.0.yaml
```

Review the change before applying it ([lab 08](08-upgrade.md)):

<!-- test: contains=1.1.0; output -->
```bash
helm template shop charts/bookshop --namespace bookshop-staging --skip-tests \
  -f charts/bookshop/values-staging.yaml -f labs/work/capstone/node-api-1.1.0.yaml \
  | kubectl diff --server-side --field-manager=helm --namespace bookshop-staging -f - 2>/dev/null \
  | grep -E '^[-+] ' | grep -vE 'generation:|meta\.helm\.sh/|^-\s+annotations:$|DB_PASSWORD' || true
```

```text
-    app.kubernetes.io/version: 1.0.0
+    app.kubernetes.io/version: 1.1.0
-        app.kubernetes.io/version: 1.0.0
+        app.kubernetes.io/version: 1.1.0
-        image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
+        image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.1.0
-    app.kubernetes.io/version: 1.0.0
+    app.kubernetes.io/version: 1.1.0
```

Only node-api's image and version label change (the Secret is filtered out: `helm template` renders a fresh random
password every time, while the real upgrade keeps the existing one via `lookup`, [lab 06](06-rendering.md)).

<!-- test: timeout=600; contains=STATUS: deployed -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-staging \
  -f charts/bookshop/values-staging.yaml -f labs/work/capstone/node-api-1.1.0.yaml \
  --wait --timeout 5m | grep -E '^(STATUS|REVISION):'
```

<!-- test: timeout=300; contains="version":"1.1.0"; output -->
```bash
kubectl rollout status deployment/shop-node-api --namespace bookshop-staging
helm test shop --namespace bookshop-staging --logs | grep node-api
```

```text
deployment "shop-node-api" successfully rolled out
node-api: {"status":"ready","service":"node-api","version":"1.1.0"}
```

## Expected Output

- Step 11: `STATUS: deployed`, revision 1, NOTES listing five services and the staging host.
- Step 13: revision 2, node-api reports `"version":"1.1.0"`.
- Step 16: revision 4, `Rollback to 2`, node-api still 1.1.0, java-api back to 1.0.0.

## Explanation

The workflow you just ran is the one teams run every week: a values change (here the release overlay), reviewed as a
diff, applied with `--wait`, verified by a test. Raw YAML gave you none of the safety rails: no review diff tied to a
release, no history, no rollback of the whole application, no test.

## Break It

### 14 · Break the upgrade

Someone promotes java-api `2.0.0` before it was published:

<!-- test: fail; timeout=600; contains=UPGRADE FAILED; output=tail:2 -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-staging \
  -f charts/bookshop/values-staging.yaml -f labs/work/capstone/node-api-1.1.0.yaml \
  --set services.java-api.image.tag=2.0.0 --wait --timeout 90s
```

```text
...
Error: UPGRADE FAILED: resource Deployment/bookshop-staging/shop-java-api not ready. status: InProgress, message: Pending termination: 1
context deadline exceeded
```

## Troubleshoot It

### 15 · Troubleshoot

<!-- test: contains=bookshop-java-api:2.0.0; output -->
```bash
bash troubleshooting/triage.sh shop bookshop-staging | sed -n '/== helm history/,/== values/p;/== warning events/,$p'
```

```text
== helm history (last 3)
REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION                                                         
1       	Mon Oct  5 00:35:13 2026	superseded	bookshop-1.2.0	1.0.0      	Install complete                                                    
2       	Mon Oct  5 00:35:41 2026	deployed  	bookshop-1.2.0	1.0.0      	Upgrade complete                                                    
3       	Mon Oct  5 00:35:54 2026	failed    	bookshop-1.2.0	1.0.0      	Upgrade "shop" failed: resource Deployment/bookshop-staging/shop-jav

== values supplied by the user
== warning events of the release's objects (last 8)
shop-node-api-64f4cb4bcf-ms4j6     Unhealthy   Readiness probe failed: Get "http://10.244.1.135:3000/ready": context deadline exceeded (Client.Timeout exceeded 
shop-node-api-64f4cb4bcf-d4h9w     Unhealthy   Readiness probe failed: HTTP probe failed with statuscode: 503
shop-java-api-f7bcdfdd7-9ffn5      Unhealthy   Readiness probe failed: Get "http://10.244.1.134:8080/ready": context deadline exceeded (Client.Timeout exceeded 
shop-node-api-688cc5c85f-xhzjk     Unhealthy   Readiness probe failed: Get "http://10.244.1.144:3000/ready": dial tcp 10.244.1.144:3000: connect: connection ref
shop-node-api-688cc5c85f-4vjvt     Unhealthy   Readiness probe failed: Get "http://10.244.1.145:3000/ready": dial tcp 10.244.1.145:3000: connect: connection ref
shop-java-api-5dd4d8bfd7-g62rl     Failed      Error: ErrImagePull
shop-java-api-5dd4d8bfd7-g62rl     Failed      Failed to pull image "ghcr.io/sufyanahmadkamboh/bookshop-java-api:2.0.0": rpc error: code = NotFound desc = faile
shop-java-api-5dd4d8bfd7-g62rl     Failed      Error: ImagePullBackOff
```

The history shows revision 3 `failed`; the events show `bookshop-java-api:2.0.0` cannot be pulled. The rest of the
platform is untouched and the old java-api Pod keeps serving: the rolling update waits for a Ready new Pod.

### 16 · Roll back

Revision 2 (node-api 1.1.0, everything else 1.0.0) is the last good state:

<!-- test: timeout=600; contains=Rollback was a success -->
```bash
helm rollback shop 2 --namespace bookshop-staging --wait --timeout 5m
```

## Challenge

Promote the **same** tested state to production the way a release process would: package the chart as version
`1.2.1` (its contents now carry node-api 1.1.0 for production as a reviewed values overlay), install it into
`bookshop-prod` from the package, and gate it with the Helm test.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: timeout=900; contains=Phase:          Succeeded; output=tail:3 -->
```bash
helm package charts/bookshop --version 1.2.1 --destination labs/work/capstone > /dev/null
helm upgrade --install shop labs/work/capstone/bookshop-1.2.1.tgz --namespace bookshop-prod --create-namespace \
  -f charts/bookshop/values-prod.yaml -f labs/work/capstone/node-api-1.1.0.yaml --wait --timeout 10m > /dev/null
helm test shop --namespace bookshop-prod
```

```text
...
Last Started:   Mon Oct  5 00:37:54 2026
Last Completed: Mon Oct  5 00:37:55 2026
Phase:          Succeeded
```

`helm list` now shows `bookshop-1.2.1` in production and `bookshop-1.2.0` in staging: the chart version tells you
exactly which package each environment runs. In a real setup, the package goes to a registry ([lab 11](11-repositories.md))
and production installs `oci://.../bookshop --version 1.2.1`.

</details>

## Verification

### 17 · Run the Helm test

<!-- test: timeout=300; contains=all checks passed; contains=1.1.0; output -->
```bash
helm test shop --namespace bookshop-staging --logs | sed -n '/POD LOGS/,$p'
```

```text
POD LOGS: shop-test-services (check)
frontend: {"status":"ok","service":"frontend","version":"1.0.0"}
go-status: {"service":"go-status","status":"ok","version":"1.0.0"}
java-api: {"status":"ready","service":"java-api","version":"1.0.0"}
node-api: {"status":"ready","service":"node-api","version":"1.1.0"}
python-api: {"status":"ready","service":"python-api","version":"1.0.0"}
frontend environment: staging
all checks passed
```

### 18 · Review the release history

<!-- test: contains=Rollback to 2; output -->
```bash
helm history shop --namespace bookshop-staging | cut -c1-120
helm list --all-namespaces --filter '^shop$'
```

```text
REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION                                     
1       	Mon Oct  5 00:35:13 2026	superseded	bookshop-1.2.0	1.0.0      	Install complete                                
2       	Mon Oct  5 00:35:41 2026	superseded	bookshop-1.2.0	1.0.0      	Upgrade complete                                
3       	Mon Oct  5 00:35:54 2026	failed    	bookshop-1.2.0	1.0.0      	Upgrade "shop" failed: resource Deployment/books
4       	Mon Oct  5 00:37:26 2026	deployed  	bookshop-1.2.0	1.0.0      	Rollback to 2                                   
NAME	NAMESPACE       	REVISION	UPDATED                               	STATUS  	CHART         	APP VERSION
shop	bookshop-prod   	1       	2026-10-05 00:37:26.8396509 +0200 CEST	deployed	bookshop-1.2.1	1.0.0      
shop	bookshop-staging	4       	2026-10-05 00:37:26.2333669 +0200 CEST	deployed	bookshop-1.2.0	1.0.0      
shop	bookshop-dev    	28      	2026-10-05 00:20:12.067319 +0200 CEST 	deployed	bookshop-1.2.0	1.0.0      
```

Read it as the story of the week: installed (1), node-api 1.1.0 (2), a failed java-api promotion (3), rolled back to
2 (4). Nothing about this needed a meeting to reconstruct.

## Cleanup

### 19 · Clean up

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls every shop release, deletes the namespaces, their database volumes and the kept
password Secrets.
```

<!-- test: timeout=900; contains=uninstalled -->
```bash
for ns in bookshop-dev bookshop-staging bookshop-prod; do
  helm uninstall shop --namespace $ns --wait 2>/dev/null
  kubectl delete namespace $ns --wait=false > /dev/null 2>&1
done
rm -rf labs/work/capstone
```

`helm uninstall` left the `shop-db` Secrets (`helm.sh/resource-policy: keep`) and the database volumes (StatefulSet
claims): deleting the namespaces removes them. In a real environment, that is the moment to be sure: it deletes data.

<!-- test: retry=60; absent=bookshop-; output -->
```bash
helm list --all-namespaces
kubectl get namespaces
```

```text
NAME   	NAMESPACE	REVISION	UPDATED                               	STATUS  	CHART         	APP VERSION
traefik	traefik  	1       	2026-10-04 22:21:36.5148655 +0200 CEST	deployed	traefik-41.6.1	v3.7.13    
NAME                 STATUS   AGE
default              Active   136m
kube-node-lease      Active   136m
kube-public          Active   136m
kube-system          Active   136m
local-path-storage   Active   136m
traefik              Active   136m
```

You took an application from 1,374 lines of copied YAML to a chart with three short environment files, and operated
it through a complete release lifecycle. Final step: [cleanup](cleanup.md) of the cluster itself, and the
[challenges](../challenges/README.md).
