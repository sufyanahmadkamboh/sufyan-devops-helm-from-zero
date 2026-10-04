# Lab 12 · Chart dependencies

> Level 14. Time: 45 minutes.

## Objective

Build and install charts that contain other charts: a parent chart with a dependency from a public repository, and
the production-style Bookshop chart with its own PostgreSQL chart as a dependency.

## Prerequisites

- [Lab 11](11-repositories.md) (the `podinfo` repository is added).

## Task

1. Download the dependency of [examples/dependency-example](../examples/dependency-example) and install it.
2. Configure the dependency from the parent's values; switch it off with its condition.
3. Install [charts/bookshop](../charts/bookshop) for dev, with its local `postgres` dependency.

## Commands

### 1 · Parent and child

```text
storefront (parent chart)                       bookshop (parent chart)
 ├── templates/configmap.yaml                    ├── templates/  (5 services, config, secret, ingress, hook, test)
 └── dependency: podinfo 6.15.0                  └── dependency: postgres 0.1.1
       from https://stefanprodan.github.io/podinfo      from file://../postgres (this repository)
       alias: catalog, condition: catalog.enabled        condition: postgres.enabled
```

The dependency is declared in the parent's `Chart.yaml`:

<!-- test: contains=alias: catalog; output -->
```bash
sed -n '/^dependencies:/,$p' examples/dependency-example/Chart.yaml
```

```text
dependencies:
  - name: podinfo                                      # the chart's name in the repository
    version: 6.15.0                                    # pinned: an exact version, never a floating range in production
    repository: https://stefanprodan.github.io/podinfo # where "helm dependency update" downloads it from
    alias: catalog                                     # the name inside this chart: values live under "catalog:"
    condition: catalog.enabled                         # catalog.enabled=false leaves it out entirely
```

| Field | Meaning |
|---|---|
| `name`, `version` | which chart, which version (pin it exactly) |
| `repository` | where to get it: `https://...` (repository), `oci://...` (registry), `file://...` (a folder) |
| `alias` | the name inside the parent: objects are named `<release>-catalog`, values live under `catalog:` |
| `condition` | a value that switches the dependency on or off |

### 2 · Download it

Declared is not downloaded. The dependency must be in the parent's `charts/` folder:

<!-- test-run: rm -rf examples/dependency-example/charts -->

<!-- test: contains=missing; output -->
```bash
helm dependency list examples/dependency-example
```

```text
NAME   	VERSION	REPOSITORY                            	STATUS 
podinfo	6.15.0 	https://stefanprodan.github.io/podinfo	missing
```

<!-- test: timeout=120; contains=Saving 1 charts; output -->
```bash
helm dependency update examples/dependency-example
```

```text
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "podinfo" chart repository
...Successfully got an update from the "traefik" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Downloading podinfo from repo https://stefanprodan.github.io/podinfo
Deleting outdated charts
```

<!-- test: contains=podinfo-6.15.0.tgz; contains=ok; output -->
```bash
ls examples/dependency-example/charts/
helm dependency list examples/dependency-example
cat examples/dependency-example/Chart.lock
```

```text
podinfo-6.15.0.tgz
NAME   	VERSION	REPOSITORY                            	STATUS
podinfo	6.15.0 	https://stefanprodan.github.io/podinfo	ok    

dependencies:
- name: podinfo
  repository: https://stefanprodan.github.io/podinfo
  version: 6.15.0
digest: sha256:4db004e2ef9fcf6bc9b31b8e78f026d003127f371e820cc4f620f1104b204554
generated: "2026-10-04T23:13:45.2821502+02:00"
```

| Command | Does | When |
|---|---|---|
| `helm dependency update` | resolves the versions in `Chart.yaml`, downloads them, **rewrites `Chart.lock`** | you changed a dependency |
| `helm dependency build` | downloads exactly what `Chart.lock` says | a fresh clone, CI |

Commit `Chart.lock` (exact versions + a digest) so everyone builds the same thing. This repository does **not**
commit the downloaded `.tgz` files ([.gitignore](../.gitignore)); `helm dependency build` recreates them.

### 3 · Install, and configure the child from the parent

The parent's [values.yaml](../examples/dependency-example/values.yaml) sets podinfo's values under the alias
`catalog:` (the message, the Ingress host). The child never sees the parent's other values.

<!-- test: timeout=300; contains=STATUS: deployed; output=head:6 -->
```bash
helm install shopfront examples/dependency-example --namespace lab-12 --create-namespace --wait --timeout 3m
```

```text
NAME: shopfront
LAST DEPLOYED: Sun Oct  4 23:44:58 2026
NAMESPACE: lab-12
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

<!-- test: retry=20; contains=deployed as a dependency; output -->
```bash
kubectl get deploy,svc --namespace lab-12
kubectl get configmap shopfront-storefront --namespace lab-12 -o jsonpath='{.data.CATALOG_URL}'; echo
curl -s http://catalog.localhost:8080/ | grep '"message"'
```

```text
http://shopfront-catalog:9898
  "message": "catalog service, deployed as a dependency of storefront",
```

One release, objects from two charts. The parent's ConfigMap points at the child's Service by name. Helm records the
dependency (by its alias) in the release:

<!-- test: contains=DEPENDENCIES: catalog; output -->
```bash
helm get metadata shopfront --namespace lab-12 | grep -E '^(CHART|VERSION|DEPENDENCIES)'
```

```text
CHART: storefront
VERSION: 0.1.0
DEPENDENCIES: catalog
```

Switch the dependency off with its condition:

<!-- test: timeout=300; contains=CATALOG_URL=; absent=shopfront-catalog; output -->
```bash
helm upgrade shopfront examples/dependency-example --namespace lab-12 --set catalog.enabled=false --wait > /dev/null
kubectl get deploy --namespace lab-12 2>&1
echo "CATALOG_URL=$(kubectl get configmap shopfront-storefront --namespace lab-12 -o jsonpath='{.data.CATALOG_URL}')"
```

```text
No resources found in lab-12 namespace.
CATALOG_URL=
```

The podinfo objects are gone, and the parent's template reacted to the same value (`CATALOG_URL` is empty).

### 4 · The Bookshop chart and its database

[charts/bookshop](../charts/bookshop) depends on [charts/postgres](../charts/postgres), a small chart in this
repository (`repository: file://../postgres`). A fresh clone has no `charts/bookshop/charts/` folder; build it from the
lock file:

<!-- test: contains=postgres-0.1.1.tgz; output -->
```bash
helm dependency build charts/bookshop
ls charts/bookshop/charts/
```

```text
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "podinfo" chart repository
...Successfully got an update from the "traefik" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
postgres-0.1.0.tgz
```

Install the whole platform for dev (the first install pulls six images; give it a few minutes):

<!-- test: timeout=600; contains=STATUS: deployed; output -->
```bash
helm upgrade --install shop charts/bookshop \
  --namespace bookshop-dev --create-namespace \
  -f charts/bookshop/values-dev.yaml \
  --wait --timeout 8m
```

```text
Release "shop" does not exist. Installing it now.
NAME: shop
LAST DEPLOYED: Sun Oct  4 23:45:03 2026
NAMESPACE: bookshop-dev
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
Bookshop 1.0.0 (chart 1.2.0) · release "shop" · namespace "bookshop-dev" · environment dev · revision 1

Services:
  frontend    ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0 × 1
  go-status   ghcr.io/sufyanahmadkamboh/bookshop-go-status:1.0.0 × 1
  java-api    ghcr.io/sufyanahmadkamboh/bookshop-java-api:1.0.0 × 1
  node-api    ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0 × 1
  python-api  ghcr.io/sufyanahmadkamboh/bookshop-python-api:1.0.0 × 1
Database:    bundled (shop-postgres) · password in Secret "shop-db"

Open:  http://dev.bookshop.localhost:8080/

Check it:
  kubectl --namespace bookshop-dev get pods -l app.kubernetes.io/instance=shop
  kubectl --namespace bookshop-dev logs job/shop-report      # the post-install report
  helm test shop --namespace bookshop-dev
```

<!-- test: contains=shop-postgres-0; absent=Error; absent=CrashLoopBackOff; output -->
```bash
kubectl get pods --namespace bookshop-dev
```

```text
NAME                              READY   STATUS      RESTARTS   AGE
shop-frontend-5d865884c8-dwdzh    1/1     Running     0          27s
shop-go-status-6dc7845b99-hsp7x   1/1     Running     0          27s
shop-java-api-7ff96666d4-hvlqq    1/1     Running     0          27s
shop-node-api-fbb58c4c4-lxn7v     1/1     Running     0          27s
shop-postgres-0                   1/1     Running     0          27s
shop-python-api-9f4bcbc58-6wn2x   1/1     Running     0          27s
shop-report-cmdk6                 0/1     Completed   0          3s
```

<!-- test: retry=20; contains=Ada Lovelace; contains=APP_ENV: "dev"; output -->
```bash
curl -s http://dev.bookshop.localhost:8080/config.js; echo
curl -s http://dev.bookshop.localhost:8080/api/users | head -c 120; echo
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

[{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-10-04T21:45:14.351Z"},{"id":2,"name":"Grace 
```

Open <http://dev.bookshop.localhost:8080/>: the full Bookshop, every panel green. Seven workloads from two charts,
one release, one command. Compare with Level 1.

## Expected Output

- `helm dependency list`: status `missing` before, `ok` after `helm dependency update`.
- `curl catalog.localhost`: `"message": "catalog service, deployed as a dependency of storefront"`.
- Bookshop: 7 Pods Running (5 services, `shop-postgres-0`, the completed `shop-report` hook Pod), users from the API.

## Explanation

When is a dependency the right tool?

| Use a dependency | Use separate releases |
|---|---|
| The component exists only for this application (its own database, a cache) | Shared infrastructure (one ingress controller, one monitoring stack for all apps) |
| It must be installed, upgraded and removed together with the app | It has its own lifecycle, owner or upgrade schedule |
| You want one `helm install` for a complete environment (dev, CI, demos) | Production databases (often managed services, or an operator) |

The bookshop's bundled PostgreSQL is perfect for dev and CI. In production you would likely set
`postgres.enabled=false` and point `database.host` at a managed database: the condition makes that a values change,
not a chart change.

Subchart values flow **down only**: the parent sets `catalog.*` (or `postgres.*`); a child cannot read the parent's
values, except the special `global:` key, which every chart in the tree sees.

## Break It

A colleague clones the repository and installs the example straight away:

<!-- test-run: rm -rf labs/work/fresh-clone && mkdir -p labs/work && cp -r examples/dependency-example labs/work/fresh-clone && rm -rf labs/work/fresh-clone/charts -->

<!-- test: fail; contains=missing in charts/ directory; output -->
```bash
helm install broken labs/work/fresh-clone --namespace lab-12 --dry-run=client
```

```text
Error: INSTALLATION FAILED: an error occurred while checking for chart dependencies. You may need to run 'helm dependency build' to fetch missing dependencies: found in Chart.yaml, but missing in charts/ directory: podinfo
```

## Troubleshoot It

The error names the missing dependency. `helm dependency list` confirms the status, and `build` (not `update`: the
lock file says exactly what to fetch) repairs it:

<!-- test: timeout=120; contains=ok; output -->
```bash
helm dependency list labs/work/fresh-clone | tail -2
helm dependency build labs/work/fresh-clone > /dev/null
helm dependency list labs/work/fresh-clone | tail -2
```

```text
podinfo	6.15.0 	https://stefanprodan.github.io/podinfo	missing

podinfo	6.15.0 	https://stefanprodan.github.io/podinfo	ok    
```

In CI, run `helm dependency build` before lint, template or package: this repository's workflow does.

## Challenge

Through the **parent's** values only (no change to the podinfo chart): switch the catalog back on, with **two**
replicas and the message `catalog v2`. Then prove where each value ended up.

## Solution

<details>
<summary>Open the solution</summary>

Everything under the alias is handed to the child as its own values:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade shopfront examples/dependency-example --namespace lab-12 \
  --set catalog.enabled=true --set catalog.replicaCount=2 --set catalog.ui.message="catalog v2" \
  --wait --timeout 3m | grep STATUS
```

</details>

## Verification

<!-- test: retry=20; contains=catalog v2; contains=2/2; output -->
```bash
kubectl get deploy shopfront-catalog --namespace lab-12
curl -s http://catalog.localhost:8080/ | grep '"message"'
```

```text
NAME                READY   UP-TO-DATE   AVAILABLE   AGE
shopfront-catalog   2/2     2            2           12s
  "message": "catalog v2",
```

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls shopfront and deletes the namespace lab-12.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall shopfront --namespace lab-12 --wait
kubectl delete namespace lab-12 --wait=false > /dev/null
rm -rf labs/work/fresh-clone
```

Keep the `shop` release in `bookshop-dev`: labs 13 and 14 use it.

Next: [lab 13 · Hooks](13-hooks.md).
