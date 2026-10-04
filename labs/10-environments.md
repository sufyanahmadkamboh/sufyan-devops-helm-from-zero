# Lab 10 · Multiple environments

> Level 12. Time: 40 minutes. One of the most important labs: this is what Helm is used for every day.

## Objective

Run one chart as three environments (dev, staging, prod) from three small values files, compare them, and
understand which differences belong in values files and which do not.

## Prerequisites

- [Lab 08](08-upgrade.md): release `demo` in `demo-dev` with the dev values.

## Task

1. Deploy staging and production next to dev, with `helm upgrade --install`.
2. Compare the three environments from Helm's and from Kubernetes' point of view.
3. Find a values-order mistake.

## Commands

### 1 · The values files

```text
values.yaml              defaults: everything the chart needs, safe for a laptop
  ├── values-dev.yaml       environment: dev,     1 replica,                host demo-dev.localhost
  ├── values-staging.yaml   environment: staging, 2 replicas,               host demo-staging.localhost
  └── values-prod.yaml      environment: prod,    pinned tag, autoscaling 3–6, more CPU/memory, host demo.localhost
```

<!-- test: contains=replicaCount: 2; output -->
```bash
for env in dev staging prod; do echo "# --- values-$env.yaml"; grep -v '^#' charts/demo-app/values-$env.yaml; done
```

```text
# --- values-dev.yaml
environment: dev
replicaCount: 1
ingress:
  enabled: true
  hosts:
    - host: demo-dev.localhost
      paths:
        - path: /
          pathType: Prefix
# --- values-staging.yaml
environment: staging
replicaCount: 2
ingress:
  enabled: true
  hosts:
    - host: demo-staging.localhost
      paths:
        - path: /
          pathType: Prefix
# --- values-prod.yaml
environment: prod
image:
  tag: "1.0.0"                 # pinned explicitly: production never follows a default
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 6
  targetCPUUtilizationPercentage: 70
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 500m
    memory: 256Mi
ingress:
  enabled: true
  hosts:
    - host: demo.localhost
      paths:
        - path: /
          pathType: Prefix
```

Each file contains **only what differs** from the defaults: 9 lines for dev, 9 for staging, 22 for prod. Compare with Level 1,
where each environment was 460 lines.

### 2 · Deploy staging and production

`helm upgrade --install` installs when the release does not exist and upgrades when it does: the same command for the
first and the hundredth deployment, which is why pipelines use it.

<!-- test: timeout=300; contains=STATUS: deployed; output=head:6 -->
```bash
helm upgrade --install demo charts/demo-app \
  --namespace demo-staging --create-namespace \
  -f charts/demo-app/values-staging.yaml \
  --wait --timeout 3m
```

```text
Release "demo" does not exist. Installing it now.
NAME: demo
LAST DEPLOYED: Sun Oct  4 23:39:25 2026
NAMESPACE: demo-staging
STATUS: deployed
REVISION: 1
...
```

<!-- test: timeout=300; contains=STATUS: deployed; output=head:6 -->
```bash
helm upgrade --install demo charts/demo-app \
  --namespace demo-prod --create-namespace \
  -f charts/demo-app/values-prod.yaml \
  --wait --timeout 3m
```

```text
Release "demo" does not exist. Installing it now.
NAME: demo
LAST DEPLOYED: Sun Oct  4 23:39:26 2026
NAMESPACE: demo-prod
STATUS: deployed
REVISION: 1
...
```

Three releases of one chart, all named `demo`, one per namespace:

<!-- test: contains=demo-staging; contains=demo-prod; output -->
```bash
helm list --all-namespaces --filter '^demo$'
```

```text
NAME	NAMESPACE    	REVISION	UPDATED                               	STATUS         	CHART         	APP VERSION
demo	demo-rollback	5       	2026-10-04 23:38:41.1761555 +0200 CEST	pending-upgrade	demo-app-1.0.0	1.0.0      
demo	demo-staging 	1       	2026-10-04 23:39:25.3244092 +0200 CEST	deployed       	demo-app-1.0.0	1.0.0      
demo	demo-dev     	7       	2026-10-04 23:32:13.2152123 +0200 CEST	deployed       	demo-app-1.0.0	1.0.0      
demo	demo-prod    	1       	2026-10-04 23:39:26.8553602 +0200 CEST	deployed       	demo-app-1.0.0	1.0.0      
```

### 3 · Compare

The Kubernetes side, across namespaces, selected by the chart's labels:

<!-- test: retry=30; contains=3/3; output -->
```bash
kubectl get deployments --all-namespaces -l app.kubernetes.io/name=demo-app -L environment
kubectl get hpa --all-namespaces
```

```text
NAMESPACE       NAME            READY   UP-TO-DATE   AVAILABLE   AGE    ENVIRONMENT
demo-dev        demo-demo-app   1/1     1            1           9m7s   dev
demo-prod       demo-demo-app   3/3     3            3           0s     prod
demo-rollback   demo-demo-app   1/1     1            1           116s   dev
demo-staging    demo-demo-app   2/2     2            2           2s     staging
NAMESPACE   NAME            REFERENCE                  TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
demo-prod   demo-demo-app   Deployment/demo-demo-app   cpu: <unknown>/70%   3         6         1          1s
```

Production has a HorizontalPodAutoscaler that keeps between 3 and 6 replicas. Its CPU target shows `<unknown>`: kind
has no metrics-server, so the HPA cannot measure CPU, but it still enforces the minimum of 3.

<!-- test: retry=20; contains=APP_ENV: "staging"; contains=APP_ENV: "prod"; output -->
```bash
for host in demo-dev demo-staging demo; do
  printf '%-14s ' "$host"; curl -s "http://$host.localhost:8080/config.js"; echo
done
```

```text
demo-dev       window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

demo-staging   window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "staging" };

demo           window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "prod" };
```

The resources per environment (production gets more, and pins the image tag):

<!-- test: contains=500m; output -->
```bash
for ns in demo-dev demo-staging demo-prod; do
  printf '%-13s ' "$ns"
  kubectl get deployment demo-demo-app --namespace $ns \
    -o jsonpath='{.spec.template.spec.containers[0].image}{"  "}{.spec.template.spec.containers[0].resources}{"\n"}'
done
```

```text
demo-dev      ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0  {"limits":{"cpu":"200m","memory":"128Mi"},"requests":{"cpu":"10m","memory":"32Mi"}}
demo-staging  ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0  {"limits":{"cpu":"200m","memory":"128Mi"},"requests":{"cpu":"10m","memory":"32Mi"}}
demo-prod     ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0  {"limits":{"cpu":"500m","memory":"256Mi"},"requests":{"cpu":"50m","memory":"64Mi"}}
```

The Helm side: what differs between staging and production, exactly?

<!-- test: contains=autoscaling; output -->
```bash
diff <(helm get values demo --namespace demo-staging) <(helm get values demo --namespace demo-prod) || true
```

```text
2c2,9
< environment: staging
---
> autoscaling:
>   enabled: true
>   maxReplicas: 6
>   minReplicas: 3
>   targetCPUUtilizationPercentage: 70
> environment: prod
> image:
>   tag: 1.0.0
6c13
<   - host: demo-staging.localhost
---
>   - host: demo.localhost
10c17,23
< replicaCount: 2
---
> resources:
>   limits:
>     cpu: 500m
>     memory: 256Mi
>   requests:
>     cpu: 50m
>     memory: 64Mi
```

### 4 · What differs between environments, and where it belongs

| Difference | dev | staging | prod | Where |
|---|---|---|---|---|
| Replicas | 1 | 2 | HPA 3–6 | values file |
| Image tag | appVersion | appVersion | pinned `1.0.0` | values file (prod pins explicitly) |
| Resources | small defaults | small defaults | 50m/64Mi → 500m/256Mi | values file |
| Host name / Ingress | `demo-dev.localhost` | `demo-staging.localhost` | `demo.localhost` | values file |
| Configuration | `APP_ENV=dev` | `staging` | `prod` | values file → ConfigMap |
| Autoscaling | off | off | on | values file |
| Persistence | small volume | medium | large | values file ([bookshop](../charts/bookshop): 1Gi / 2Gi / 5Gi) |
| Passwords, keys | – | – | – | **never in a values file**: a Secret created outside the chart, referenced by name ([lab 14 + docs](../docs/12-configmaps-and-secrets.md)) |
| The templates | same | same | same | the chart: one version for all environments |

The last row is the point: every environment runs **the same chart version**. A change is tested in dev and staging
with exactly the templates that will reach production. Only values differ.

## Expected Output

- Three `deployed` releases named `demo` in `demo-dev`, `demo-staging`, `demo-prod`.
- Deployments 1/1, 2/2, 3/3; one HPA in `demo-prod`.
- Each host returns its own `APP_ENV`.

## Explanation

The model to remember:

```text
 chart (version 1.0.0) ──┬── values-dev.yaml      ──► release demo in demo-dev
                         ├── values-staging.yaml  ──► release demo in demo-staging
                         └── values-prod.yaml     ──► release demo in demo-prod
 promote = deploy the same chart version with the next environment's file
```

Alternatives you will meet: one values file per environment **and** per region (`-f values-prod.yaml -f
values-prod-eu.yaml`), values kept in a separate "deployment" repository, or a GitOps tool (Argo CD, Flux) that runs
the same `helm template` with each environment's files. The layering is the same: defaults, then environment,
then the most specific.

## Break It

A teammate wants to be "explicit" and passes the chart's defaults file too, after the staging file:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace demo-staging \
  -f charts/demo-app/values-staging.yaml -f charts/demo-app/values.yaml --wait | grep STATUS
```

<!-- test: retry=10; contains=404 page not found; output -->
```bash
curl -s http://demo-staging.localhost:8080/config.js; echo
```

```text
404 page not found
```

## Troubleshoot It

The upgrade succeeded and staging disappeared from its address. Which values does the release have now?

<!-- test: contains=environment: local; contains=No resources found; output -->
```bash
helm get values demo --namespace demo-staging | grep -E '^(environment|replicaCount):'
kubectl get ingress --namespace demo-staging 2>&1
```

```text
  enabled: false
environment: local
  enabled: false
  enabled: false
replicaCount: 1
```

Later files win. `values.yaml` came last, so its defaults (`environment: local`, `replicaCount: 1`,
`ingress.enabled: false`) overrode every staging setting. The chart's `values.yaml` is **always** applied first,
implicitly; never pass it again. Fix: the environment file alone.

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace demo-staging -f charts/demo-app/values-staging.yaml --wait | grep STATUS
```

<!-- test: retry=20; contains=APP_ENV: "staging" -->
```bash
curl -s http://demo-staging.localhost:8080/config.js; echo
```

## Challenge

Add a fourth environment, **qa**: one replica, environment `qa`, host `demo-qa.localhost`, and an admin link
`http://admin-qa.example.com`. One new file, no template change. Deploy it to namespace `demo-qa`.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
cat > labs/work/values-qa.yaml <<'EOF'
# qa: like dev, with the admin link switched on for the testers.
environment: qa
replicaCount: 1
config:
  adminUrl: http://admin-qa.example.com
ingress:
  enabled: true
  hosts:
    - host: demo-qa.localhost
      paths:
        - path: /
          pathType: Prefix
EOF
helm upgrade --install demo charts/demo-app --namespace demo-qa --create-namespace \
  -f labs/work/values-qa.yaml --wait --timeout 3m | grep STATUS
```

A new environment costs one short file. In a real repository it would sit next to the others,
`charts/demo-app/values-qa.yaml`, reviewed like any code change.

</details>

## Verification

<!-- test: retry=20; contains=APP_ENV: "qa"; output -->
```bash
curl -s http://demo-qa.localhost:8080/config.js; echo
helm list --all-namespaces --filter '^demo$'
```

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin-qa.example.com", APP_ENV: "qa" };

NAME	NAMESPACE    	REVISION	UPDATED                               	STATUS         	CHART         	APP VERSION
demo	demo-staging 	3       	2026-10-04 23:39:34.3620855 +0200 CEST	deployed       	demo-app-1.0.0	1.0.0      
demo	demo-dev     	7       	2026-10-04 23:32:13.2152123 +0200 CEST	deployed       	demo-app-1.0.0	1.0.0      
demo	demo-prod    	1       	2026-10-04 23:39:26.8553602 +0200 CEST	deployed       	demo-app-1.0.0	1.0.0      
demo	demo-qa      	1       	2026-10-04 23:39:37.285147 +0200 CEST 	deployed       	demo-app-1.0.0	1.0.0      
demo	demo-rollback	5       	2026-10-04 23:38:41.1761555 +0200 CEST	pending-upgrade	demo-app-1.0.0	1.0.0      
```

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls the four demo releases and deletes their namespaces.
```

<!-- test: timeout=600; contains=uninstalled -->
```bash
for ns in demo-dev demo-staging demo-prod demo-qa; do
  helm uninstall demo --namespace $ns --wait
  kubectl delete namespace $ns --wait=false > /dev/null
done
rm -f labs/work/values-qa.yaml
```

Next: [lab 11 · Repositories and existing charts](11-repositories.md).
