# Lab 14 · Tests, NOTES and helpers

> Level 16. Time: 35 minutes.

## Objective

Run a chart's tests, read what a test Pod does, make a test fail and investigate it. Then look at the two other
user-facing parts of a chart: the NOTES shown after installation and the helpers that keep labels consistent.

## Prerequisites

- [Lab 13](13-hooks.md): the `shop` release in `bookshop-dev`.

## Task

1. Run the Bookshop's tests and read their logs.
2. Break the application in a way Helm does not notice, and let the test find it.
3. Write an additional test.

## Commands

### 1 · What a Helm test is

A test is a Pod in `templates/tests/` with the annotation `helm.sh/hook: test`. It is not created by install or
upgrade; only `helm test` creates it. It passes if its container exits with 0.

<!-- test: contains=helm.sh/hook; output -->
```bash
sed -n '1,30p' charts/bookshop/templates/tests/test-services.yaml
```

```text
# "helm test <release>": every enabled service answers /health, the APIs reach the database (/ready),
# and the frontend serves the configured environment.
apiVersion: v1
kind: Pod
metadata:
  name: {{ .Release.Name }}-test-services
  labels:
    {{- include "bookshop.labels" (dict "root" $ "name" "test") | nindent 4 }}
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  restartPolicy: Never
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: check
      image: busybox:1.37
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
      command: ["sh", "-c"]
      args:
        - |
          set -e   # stop at the first failing check: the Pod fails, and so does "helm test"
```

The Bookshop's test calls every enabled service's readiness endpoint through its Service (for the APIs, `/ready`
also checks the database connection), and checks that the frontend received the release's environment.

### 2 · Run it

<!-- test: timeout=300; contains=Phase:          Succeeded; contains=all checks passed; output -->
```bash
helm test shop --namespace bookshop-dev --logs
```

```text
NAME: shop
LAST DEPLOYED: Sun Oct  4 23:52:53 2026
NAMESPACE: bookshop-dev
STATUS: deployed
REVISION: 9
DESCRIPTION: Upgrade complete
TEST SUITE:     shop-test-services
Last Started:   Sun Oct  4 23:53:24 2026
Last Completed: Sun Oct  4 23:53:25 2026
Phase:          Succeeded

POD LOGS: shop-test-services (check)
frontend: {"status":"ok","service":"frontend","version":"1.0.0"}
go-status: {"service":"go-status","status":"ok","version":"1.0.0"}
java-api: {"status":"ready","service":"java-api","version":"1.0.0"}
node-api: {"status":"ready","service":"node-api","version":"1.0.0"}
python-api: {"status":"ready","service":"python-api","version":"1.0.0"}
frontend environment: dev
all checks passed
```

What a passing test proves: the Services route to Ready Pods, the APIs reach PostgreSQL with the generated password,
and the configuration of **this** release reached the application. What it does not prove: that the application
is correct. A test is a deployment smoke check, not a replacement for the application's own test suite.

Where it is useful: right after every `helm upgrade` in a pipeline (`helm upgrade --install ... --wait && helm test
...`), and by an on-call engineer who wants a one-command health check of a release.

### 3 · NOTES.txt

The text printed after install and upgrade is a template too ([NOTES.txt](../charts/bookshop/templates/NOTES.txt)).
It is stored with each revision:

<!-- test: contains=dev.bookshop.localhost; output -->
```bash
helm get notes shop --namespace bookshop-dev
```

```text
NOTES:
Bookshop 1.0.0 (chart 1.2.0) · release "shop" · namespace "bookshop-dev" · environment dev · revision 9

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

Because it is a template, it can adapt. demo-app's NOTES explain how to reach the application with or without an
Ingress; `--dry-run` shows the NOTES of an install without performing it:

<!-- test: contains=port-forward; output -->
```bash
helm install preview charts/demo-app --namespace default --dry-run=client --set ingress.enabled=false | sed -n '/^NOTES:/,$p'
```

```text
NOTES:
demo-app 1.0.0 (chart 1.0.0) is deployed as release "preview" in namespace "default".
Environment: local · revision 1

No Ingress (ingress.enabled=false). Reach it with a port-forward:
  kubectl --namespace default port-forward service/preview-demo-app 8080:8080
  then open http://localhost:8080/

Check it:
  kubectl --namespace default get pods -l app.kubernetes.io/instance=preview
  helm test preview --namespace default
```

Good NOTES answer three questions for the person who just installed: what is running (versions, environment), how do
I reach it, how do I check it.

### 4 · Helpers keep labels consistent

Every Bookshop object gets its labels from one helper, `bookshop.labels` in
[_helpers.tpl](../charts/bookshop/templates/_helpers.tpl). The result: one query works across all objects of a
release, whatever their kind:

<!-- test: contains=shop-postgres; output -->
```bash
kubectl get deploy,statefulset,svc --namespace bookshop-dev -l app.kubernetes.io/instance=shop \
  -L app.kubernetes.io/name,app.kubernetes.io/version,environment
```

```text
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE     NAME         VERSION   ENVIRONMENT
deployment.apps/shop-frontend     1/1     1            1           8m23s   frontend     1.0.0     dev
deployment.apps/shop-go-status    1/1     1            1           8m23s   go-status    1.0.0     dev
deployment.apps/shop-java-api     1/1     1            1           8m23s   java-api     1.0.0     dev
deployment.apps/shop-node-api     1/1     1            1           8m23s   node-api     1.0.0     dev
deployment.apps/shop-python-api   1/1     1            1           8m23s   python-api   1.0.0     dev

NAME                             READY   AGE     NAME       VERSION   ENVIRONMENT
statefulset.apps/shop-postgres   1/1     8m23s   postgres   18.6      

NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE     NAME         VERSION   ENVIRONMENT
service/shop-frontend     ClusterIP   10.96.162.163   <none>        8080/TCP   8m23s   frontend     1.0.0     dev
service/shop-go-status    ClusterIP   10.96.253.8     <none>        8080/TCP   8m23s   go-status    1.0.0     dev
service/shop-java-api     ClusterIP   10.96.5.136     <none>        8080/TCP   8m23s   java-api     1.0.0     dev
service/shop-node-api     ClusterIP   10.96.53.27     <none>        3000/TCP   8m23s   node-api     1.0.0     dev
service/shop-postgres     ClusterIP   None            <none>        5432/TCP   8m23s   postgres     18.6      
service/shop-python-api   ClusterIP   10.96.125.171   <none>        8000/TCP   8m23s   python-api   1.0.0     dev
```

| Label | Value | Used by |
|---|---|---|
| `app.kubernetes.io/name` | the component (`node-api`) | selectors, dashboards |
| `app.kubernetes.io/instance` | the release (`shop`) | selectors: keeps two releases apart |
| `app.kubernetes.io/version` | the application version | "what runs where", monitoring |
| `app.kubernetes.io/managed-by` | `Helm` | tooling, audits |
| `helm.sh/chart` | `bookshop-1.2.0` | which chart version created it |
| `environment` | `dev` | filtering, cost reports, alerts |

The selector labels (`name` + `instance`) are a separate, smaller helper on purpose: a Deployment's selector cannot
change after creation, so it must never contain a label whose value changes, like the version.

## Expected Output

- `helm test`: `Phase: Succeeded`, one line per service, `all checks passed`.
- demo-app NOTES without an Ingress: a `kubectl port-forward` command.

## Explanation

```text
helm test shop
  └─► creates Pod shop-test-services (hook: test, delete-policy: before-hook-creation)
        └─► wget each Service, check the frontend's environment ─► exit 0 = Succeeded / non-zero = Failed
```

The test Pod stays after the run (the delete policy removes it before the **next** run), so you can read its logs
any time: `kubectl logs shop-test-services -n bookshop-dev`.

## Break It

Someone scales a service down by hand (to "save resources", or by mistake while debugging):

<!-- test: contains=scaled -->
```bash
kubectl scale deployment shop-java-api --namespace bookshop-dev --replicas=0
```

<!-- test: contains=deployed; output -->
```bash
helm status shop --namespace bookshop-dev | grep '^STATUS:'
```

```text
STATUS: deployed
```

Helm still says `deployed`: it records what it applied, it does not watch the cluster.

## Troubleshoot It

The test does watch it:

<!-- test: fail; timeout=300; contains=Phase:          Failed; output=tail:9 -->
```bash
helm test shop --namespace bookshop-dev --logs
```

```text
...
Last Completed: Sun Oct  4 23:55:42 2026
Phase:          Failed

POD LOGS: shop-test-services (check)
frontend: {"status":"ok","service":"frontend","version":"1.0.0"}
go-status: {"service":"go-status","status":"ok","version":"1.0.0"}
wget: can't connect to remote host (10.96.5.136): Connection timed out

Error: resource Pod/bookshop-dev/shop-test-services not ready. status: Failed, message: pod shop-test-services failed
```

Read the log from the bottom: the last successful check was `go-status`; the next one in the list (alphabetical
order, `java-api`) could not connect (refused or timed out). No connection to a Service address means no Ready Pod
behind it:

<!-- test: contains=0/0; output -->
```bash
kubectl get deployment shop-java-api --namespace bookshop-dev
```

```text
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
shop-java-api   0/0     0            0           10m
```

Did a Helm change do this? Compare what Helm applied (the release's manifest) with what is live, using the
same server-side diff as in [lab 08](08-upgrade.md):

<!-- test: contains=+  replicas: 1; output -->
```bash
helm get manifest shop --namespace bookshop-dev \
  | kubectl diff --server-side --field-manager=helm --namespace bookshop-dev -f - \
  | grep -E '^[-+] ' | grep -vE 'generation:|meta\.helm\.sh/|^-\s+annotations:$' || true
```

```text
-  replicas: 0
+  replicas: 1
```

The release says `replicas: 1`, the cluster has 0. The only difference between Helm's record and reality: someone
changed it outside Helm. The fix is to re-apply the release's desired state:

<!-- test: timeout=600; contains=STATUS: deployed -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-dev -f charts/bookshop/values-dev.yaml --wait --timeout 5m | grep STATUS
```

<!-- test: timeout=300; contains=all checks passed -->
```bash
helm test shop --namespace bookshop-dev --logs | tail -3
```

Lesson: changes made with kubectl behind Helm's back are **drift**. Helm does not see them; `helm test` and
`helm upgrade` (which re-applies) do.

## Challenge

Add a second test to (a copy of) the bookshop chart: through the java-api Service, `/api/books` must return at least
one book (the JSON contains `"title"`). Run **only** your new test.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test-run: rm -rf labs/work/bookshop-tests && mkdir -p labs/work && cp -r charts/bookshop labs/work/bookshop-tests -->

<!-- test: timeout=600; contains=STATUS: deployed -->
```bash
cat > labs/work/bookshop-tests/templates/tests/test-books.yaml <<'EOF'
# The catalogue is not empty: /api/books returns at least one book.
apiVersion: v1
kind: Pod
metadata:
  name: {{ .Release.Name }}-test-books
  labels:
    {{- include "bookshop.labels" (dict "root" $ "name" "test") | nindent 4 }}
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  restartPolicy: Never
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: check
      image: busybox:1.37
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
      command: ["sh", "-c"]
      args:
        - |
          set -e
          books=$(wget -qO- http://{{ .Release.Name }}-java-api:{{ (index .Values.services "java-api").port }}/api/books)
          echo "$books" | grep -q '"title"'
          echo "books found: $(echo "$books" | grep -o '"title"' | wc -l)"
EOF
helm upgrade shop labs/work/bookshop-tests --namespace bookshop-dev -f charts/bookshop/values-dev.yaml --wait --timeout 5m | grep STATUS
```

`--filter name=...` runs only the named test Pod:

<!-- test: timeout=300; contains=books found; output=tail:4 -->
```bash
helm test shop --namespace bookshop-dev --filter name=shop-test-books --logs
```

```text
...
Phase:          Succeeded

POD LOGS: shop-test-books (check)
books found: 5
```

</details>

## Verification

<!-- test: timeout=300; contains=shop-test-books; contains=shop-test-services -->
```bash
helm test shop --namespace bookshop-dev | grep -A3 'TEST SUITE'
```

## Cleanup

Back to the chart from the repository (the extra test Pod stays until deleted: hook objects are not release
resources):

<!-- test: timeout=600; contains=STATUS: deployed -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-dev -f charts/bookshop/values-dev.yaml --wait --timeout 5m | grep STATUS
kubectl delete pod shop-test-books --namespace bookshop-dev --ignore-not-found > /dev/null
rm -rf labs/work/bookshop-tests
```

Keep `shop` in `bookshop-dev`: the [troubleshooting labs](../troubleshooting/README.md) use it.

Next: [Level 17 · Security](../docs/13-security.md), then [lab 15 · Troubleshooting](15-troubleshooting.md).
