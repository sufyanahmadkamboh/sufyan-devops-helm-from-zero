# Level 19 · A production-style chart

> Time: 40 minutes. Needs the `shop` release in `bookshop-dev` ([lab 12](../labs/12-dependencies.md)). The commands
> are tested like the labs.

[charts/bookshop](../charts/bookshop) packages the whole Bookshop platform from Level 1: five services, a database, an
Ingress, configuration and a password. This lesson reads it as a design: which Helm feature solves which problem of the
1,374 lines of raw YAML, and why.

## From raw YAML to chart

| Raw YAML (`environments/<env>/`) | Chart (`charts/bookshop/`) | Technique |
|---|---|---|
| `deployments.yaml` + `services.yaml`: 5 near-identical blocks each | `templates/services.yaml`: **one** block | `range` over `.Values.services` |
| per-environment replicas, resources, image tags | `values-<env>.yaml` | values files layered on `values.yaml` |
| `configmap.yaml` with hand-written service URLs | `templates/configmap.yaml` | URLs built from the release name and ports; `TARGETS` built with `range` |
| `secret.yaml` with a password in Git | `templates/secret.yaml` | generated + `lookup`, or `existingSecret` |
| `database.yaml` (StatefulSet + Service) | `charts/postgres` dependency | subchart with a `condition` |
| `ingress.yaml` with 5 paths | `templates/ingress.yaml` | `range` over `ingress.paths`, ports looked up with `index` |
| labels typed by hand, slightly different everywhere | `_helpers.tpl` | one `bookshop.labels` helper, `dict` to pass context |
| (missing) | `report-hook.yaml`, `tests/`, `NOTES.txt` | hook, test, notes |
| (missing) | `autoscaling.yaml` | HPA + PDBs, off by default, on in prod |

<!-- test: output -->
```bash
wc -l environments/*/*.yaml | tail -1
cat charts/bookshop/templates/*.yaml charts/bookshop/templates/_helpers.tpl charts/bookshop/templates/tests/*.yaml | wc -l
```

```text
 1374 total
351
```

## The design decisions

### One template for every service

[templates/services.yaml](../charts/bookshop/templates/services.yaml) ranges over the `services` map. Each entry
carries only what differs between services: image name, port, user ID, probes, resources, whether it needs the
database:

<!-- test: contains=java-api; output -->
```bash
sed -n '/^  java-api:/,/^$/p' charts/bookshop/values.yaml
```

```text
  java-api:
    enabled: true
    image: { name: bookshop-java-api, tag: "" }
    replicas: 1
    port: 8080
    runAsUser: 10001
    database: true
    probes: { liveness: /health, readiness: /ready, startup: /health }   # the JVM starts slowly: a startup probe
    resources:
      requests: { cpu: 250m, memory: 256Mi }
      limits: { cpu: "1", memory: 512Mi }
```

Adding a sixth service is an entry in `values.yaml`, not 60 lines of YAML. A service can be switched off per
environment (`services.go-status.enabled: false`) and everything that refers to it (Ingress paths, `TARGETS`, the
test) adapts, because those templates range over the same map.

### Helpers with more than one argument

Templates inside `range` need both the loop variable and the root context (`$`). The helpers take a `dict`:

<!-- test: contains=dict; output -->
```bash
grep -nE '\$ctx :=|include "bookshop.labels"' charts/bookshop/templates/services.yaml
```

```text
7:{{- $ctx := dict "root" $ "name" $name "version" $svc.image.tag }}
14:    {{- include "bookshop.labels" $ctx | nindent 4 }}
26:        {{- include "bookshop.labels" $ctx | nindent 8 }}
87:    {{- include "bookshop.labels" $ctx | nindent 4 }}
```

### Values that are templates

The frontend's nginx needs fully qualified service URLs that contain the release name and namespace, which a values
file cannot know. Values may contain template expressions; the chart renders them with `tpl`:

<!-- test: contains=svc.cluster.local; output -->
```bash
grep -n 'NODE_API_URL' charts/bookshop/values.yaml
helm template shop charts/bookshop --namespace bookshop-dev --show-only templates/services.yaml | grep -A1 'NODE_API_URL'
```

```text
25:      NODE_API_URL: "http://{{ .Release.Name }}-node-api.{{ .Release.Namespace }}.svc.cluster.local:3000"
            - name: NODE_API_URL
              value: "http://shop-node-api.bookshop-dev.svc.cluster.local:3000"
```

### A password nobody types

[templates/secret.yaml](../charts/bookshop/templates/secret.yaml): random on first install, read back with `lookup` on
upgrades, kept on uninstall (`helm.sh/resource-policy: keep`) because the database volume outlives the release.
Production replaces it with `database.existingSecret` ([security](13-security.md#safe-patterns)).

### Config changes restart Pods

Every Deployment carries `checksum/config`, a hash of the rendered ConfigMap: change a setting and every service
rolls; change nothing and nothing restarts.

## Three environments, one chart version

Dev runs since lab 12. Add staging and production:

<!-- test: timeout=900; contains=STATUS: deployed -->
```bash
for env in staging prod; do
  helm upgrade --install shop charts/bookshop --namespace bookshop-$env --create-namespace \
    -f charts/bookshop/values-$env.yaml --wait --timeout 10m | grep -E '^(NAMESPACE|STATUS):'
done
```

What each environment consists of:

<!-- test: contains=PodDisruptionBudget; output -->
```bash
for env in dev staging prod; do
  echo "== $env: $(helm get manifest shop --namespace bookshop-$env | grep -E '^kind:' | sort | uniq -c | awk '{printf "%s %s, ", $1, $3}')"
done
```

```text
== dev: 1 ConfigMap, 5 Deployment, 1 Ingress, 1 Secret, 6 Service, 1 StatefulSet, 
== staging: 1 ConfigMap, 5 Deployment, 1 Ingress, 1 Secret, 6 Service, 1 StatefulSet, 
== prod: 1 ConfigMap, 5 Deployment, 1 HorizontalPodAutoscaler, 1 Ingress, 5 PodDisruptionBudget, 1 Secret, 6 Service, 1 StatefulSet, 
```

<!-- test: retry=30; contains=bookshop-prod; output -->
```bash
kubectl get deployments --all-namespaces -l app.kubernetes.io/part-of=bookshop \
  -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,READY:.status.readyReplicas,IMAGE:.spec.template.spec.containers[0].image' \
  | grep -E 'NAMESPACE|node-api|java-api'
```

```text
NAMESPACE          NAME              READY   IMAGE
bookshop-dev       shop-java-api     1       ghcr.io/sufyanahmadkamboh/bookshop-java-api:1.0.0
bookshop-dev       shop-node-api     1       ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
bookshop-prod      shop-java-api     2       ghcr.io/sufyanahmadkamboh/bookshop-java-api:1.0.0
bookshop-prod      shop-node-api     2       ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
bookshop-staging   shop-java-api     1       ghcr.io/sufyanahmadkamboh/bookshop-java-api:1.0.0
bookshop-staging   shop-node-api     2       ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
```

<!-- test: retry=30; contains=APP_ENV: "prod"; output -->
```bash
for host in dev.bookshop staging.bookshop bookshop; do
  printf '%-18s ' "$host"; curl -s "http://$host.localhost:8080/config.js"; echo
done
```

```text
dev.bookshop       window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

staging.bookshop   window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "staging" };

bookshop           window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "prod" };
```

The tests of all three, the way a pipeline would gate a promotion:

<!-- test: timeout=600; contains=staging: Succeeded; contains=prod: Succeeded; output -->
```bash
for env in dev staging prod; do
  echo "$env: $(helm test shop --namespace bookshop-$env | grep Phase | awk '{print $2}')"
done
```

```text
dev: Succeeded
staging: Succeeded
prod: Succeeded
```

Same chart version (`bookshop-1.2.0`) everywhere; the differences are 3, 9 and 32 lines of values.

## Production extras

<!-- test: contains=shop-node-api; output -->
```bash
kubectl get hpa,pdb --namespace bookshop-prod
```

```text
NAME                                                REFERENCE                  TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/shop-node-api   Deployment/shop-node-api   cpu: <unknown>/70%   2         6         2          37s

NAME                                         MIN AVAILABLE   MAX UNAVAILABLE   ALLOWED DISRUPTIONS   AGE
poddisruptionbudget.policy/shop-frontend     1               N/A               1                     37s
poddisruptionbudget.policy/shop-go-status    1               N/A               1                     37s
poddisruptionbudget.policy/shop-java-api     1               N/A               1                     37s
poddisruptionbudget.policy/shop-node-api     1               N/A               1                     37s
poddisruptionbudget.policy/shop-python-api   1               N/A               1                     37s
```

- The HPA owns node-api's replica count (2–6); the Deployment template omits `replicas` for it.
- A PodDisruptionBudget per service keeps at least one Pod running while a node is drained.
- Pinned image tags (`image.tag: "1.0.0"`): production never follows a moving default.
- A 5 GiB volume instead of 1 GiB.

What a real production values file would add (not possible on a laptop): `database.existingSecret` from a secret
manager or `postgres.enabled: false` with a managed database, an Ingress host with TLS, resource numbers from
measurements, topology spread across availability zones.

## Versioning this chart

```text
                         chart version   app version
 today                       1.2.0          1.0.0
 node-api 1.1.0 released     1.2.1          1.0.0     only node-api's tag changes in values: services.node-api.image.tag
 all services 2.0.0          1.3.0          2.0.0     appVersion moves; templates gain what 2.0.0 needs
 selector labels changed     2.0.0          2.0.0     breaking for existing releases: major chart version
```

`appVersion` is the default for every image; a single service can move ahead with its own tag. The capstone does
exactly that with node-api 1.1.0.

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls staging and production and deletes their namespaces (and database volumes).
```

<!-- test: timeout=600; contains=uninstalled -->
```bash
for env in staging prod; do
  helm uninstall shop --namespace bookshop-$env --wait
  kubectl delete namespace bookshop-$env --wait=false > /dev/null
done
```

`shop` in `bookshop-dev` stays for the capstone.

Next, Level 20: [lab 16 · Capstone](../labs/16-capstone.md).
