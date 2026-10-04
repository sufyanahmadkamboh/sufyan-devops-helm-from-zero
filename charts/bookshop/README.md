# bookshop

The complete Bookshop platform as one production-style chart: a React frontend and four APIs (Node.js, Python, Go,
Java) from one range-driven template, PostgreSQL as a chart dependency, a generated database password, an Ingress,
a post-install/post-upgrade hook and a Helm test.

| | |
|---|---|
| Chart version | `1.2.0` |
| App version | `1.0.0` (the default tag of every Bookshop image) |
| Dependency | `postgres` `0.1.0` (local chart `../postgres`, switch: `postgres.enabled`) |

## Install

```bash
helm dependency build charts/bookshop       # puts charts/postgres-0.1.0.tgz in place (from Chart.lock)
helm upgrade --install shop charts/bookshop -n bookshop-dev --create-namespace \
  -f charts/bookshop/values-dev.yaml --wait --timeout 5m
helm test shop -n bookshop-dev
```

## What it creates (release `shop`)

| Resource | Name |
|---|---|
| Deployment + Service per service | `shop-frontend`, `shop-node-api`, `shop-python-api`, `shop-go-status`, `shop-java-api` |
| ConfigMap (settings, no secrets) | `shop-config` |
| Secret (database password) | `shop-db`, unless `database.existingSecret` is set |
| StatefulSet + Service (dependency) | `shop-postgres` |
| Ingress | `shop` (host from `ingress.host`) |
| Hook Job (post-install, post-upgrade) | `shop-report` |
| Test Pod | `shop-test-services` |
| Prod only | HPA `shop-node-api`, a PodDisruptionBudget per service |

## Important values

| Key | Default | Meaning |
|---|---|---|
| `environment` | `local` | `APP_ENV` of the UI, label on every resource |
| `imageRegistry` | `ghcr.io/sufyanahmadkamboh` | Registry of all images |
| `services.<name>.enabled` | `true` | Deploy this service |
| `services.<name>.image.tag` | `""` | Empty = `appVersion` |
| `services.<name>.replicas` | `1` | Pods of this service |
| `services.<name>.resources` | per service | Requests and limits |
| `database.existingSecret` | `""` | Name of a Secret with `DB_PASSWORD`, created outside the chart (production) |
| `database.host` | `""` | External PostgreSQL host (with `postgres.enabled: false`) |
| `postgres.enabled` | `true` | Deploy the bundled database |
| `postgres.persistence.size` | `1Gi` | Database volume |
| `ingress.host` | `bookshop.localhost` | Host name of the Ingress |
| `autoscaling.enabled` | `false` | HPA for node-api |
| `podDisruptionBudget.enabled` | `false` | One PDB (minAvailable 1) per service |
| `report.enabled` | `true` | Run the report hook after each install and upgrade |

## The database password

No password is written in any values file. Without `database.existingSecret`, the chart generates a random password
on the first install and reads it back from the cluster with `lookup` on every upgrade, so it never changes under a
running database. The Secret has `helm.sh/resource-policy: keep`: `helm uninstall` leaves it next to the database
volume, which keeps its data (and its password) too. Delete both deliberately when you want a fresh database:

```text
kubectl delete secret shop-db -n <namespace>
kubectl delete pvc data-shop-postgres-0 -n <namespace>
```
