# 09 · Secret problem

> Uses the `shop` release in `bookshop-dev`. Time: 15 minutes.

## Break it

Moving towards production practice, a teammate switches the release to an externally managed Secret, as the chart
supports ([charts/bookshop](../charts/bookshop/README.md#the-database-password)), and expects "the platform team"
to have created it:

<!-- test: fail; timeout=300; contains=UPGRADE FAILED; output=tail:2 -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-dev -f charts/bookshop/values-dev.yaml \
  --set database.existingSecret=shop-db-prod \
  --wait --timeout 90s
```

```text
...
resource Deployment/bookshop-dev/shop-python-api not ready. status: InProgress, message: Pending termination: 1
context deadline exceeded
```

## Problem

The upgrade fails after 90 seconds. The Bookshop still answers (old Pods), but the new API Pods never start.

## Symptoms

<!-- test: contains=CreateContainerConfigError; output -->
```bash
kubectl get pods --namespace bookshop-dev | grep -E 'NAME|api'
```

```text
NAME                              READY   STATUS                       RESTARTS   AGE
shop-java-api-6659d799c4-mmxq6    0/1     CreateContainerConfigError   0          90s
shop-java-api-7ff96666d4-wgr4t    1/1     Running                      0          116s
shop-node-api-689546865d-fmn4f    0/1     CreateContainerConfigError   0          90s
shop-node-api-7b995d94bd-pgfqz    1/1     Running                      0          116s
shop-python-api-57cf464-xlmz4     0/1     CreateContainerConfigError   0          90s
shop-python-api-9f4bcbc58-vjkjj   1/1     Running                      0          116s
```

## Investigation

`CreateContainerConfigError` again: a referenced object is missing. Which one, and is the reference or the object
wrong?

## Commands

<!-- test: retry=10; contains=secret "shop-db-prod" not found; output -->
```bash
kubectl get events --namespace bookshop-dev --field-selector reason=Failed \
  -o custom-columns='POD:.involvedObject.name,MESSAGE:.message' | grep node-api | grep secret | tail -2
```

```text
shop-node-api-7667b6b56b-bqm4j   Error: secret "shop-db-prod" not found
shop-node-api-784c76b5dc-56l7m   Error: secret "shop-db-prod" not found
```

<!-- test: contains=shop-db; output -->
```bash
kubectl get secrets --namespace bookshop-dev --field-selector type=Opaque
helm get values shop --namespace bookshop-dev | grep -A1 database
```

```text
NAME      TYPE     DATA   AGE
shop-db   Opaque   1      34m
database:
  existingSecret: shop-db-prod
```

## Output Interpretation

- The new Pods refer to the Secret `shop-db-prod`; it does not exist. Only `shop-db` (the chart-generated one) does.
- `helm get values` shows why: `database.existingSecret: shop-db-prod`. With that value, the chart stops creating
  its own Secret and points every service at the named one: an agreement that someone else creates it first.
- `shop-db` survived even though this revision no longer renders it: it carries `helm.sh/resource-policy: keep`.

## Root Cause

The release references a Secret that was never created. A Secret reference is a contract with whoever manages
secrets outside the chart; the contract was not fulfilled.

The tempting fix, `kubectl create secret ... --from-literal=DB_PASSWORD=something-new`, would make the Pods start
and then fail differently: PostgreSQL's data volume was initialised with the **existing** password, and a new one
would be rejected (`password authentication failed`). A Secret must contain the right value, not just exist.

## Fix

Create `shop-db-prod` with the password the database actually uses (here copied from the generated Secret; in real
life it comes from the secret manager), then upgrade with both references, the services' and the database's:

<!-- test: contains=shop-db-prod created -->
```bash
kubectl create secret generic shop-db-prod --namespace bookshop-dev \
  --from-literal=DB_PASSWORD="$(kubectl get secret shop-db --namespace bookshop-dev -o jsonpath='{.data.DB_PASSWORD}' | base64 -d)"
```

<!-- test: timeout=600; contains=STATUS: deployed -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-dev -f charts/bookshop/values-dev.yaml \
  --set database.existingSecret=shop-db-prod --set postgres.auth.existingSecret=shop-db-prod \
  --wait --timeout 5m | grep STATUS
```

## Verification

<!-- test: timeout=300; retry=3; contains=all checks passed; output=tail:7 -->
```bash
helm test shop --namespace bookshop-dev --logs
```

```text
...
frontend: {"status":"ok","service":"frontend","version":"1.0.0"}
go-status: {"service":"go-status","status":"ok","version":"1.0.0"}
java-api: {"status":"ready","service":"java-api","version":"1.0.0"}
node-api: {"status":"ready","service":"node-api","version":"1.0.0"}
python-api: {"status":"ready","service":"python-api","version":"1.0.0"}
frontend environment: dev
all checks passed
```

<!-- test: contains=shop-db-prod; output -->
```bash
kubectl get deployment shop-node-api --namespace bookshop-dev \
  -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="DB_PASSWORD")].valueFrom.secretKeyRef.name}'; echo
```

```text
shop-db-prod
```

Back to the generated Secret for the following labs (the kept `shop-db` has the same password):

<!-- test: timeout=600; contains=STATUS: deployed -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-dev -f charts/bookshop/values-dev.yaml --wait --timeout 5m | grep STATUS
kubectl delete secret shop-db-prod --namespace bookshop-dev > /dev/null
```

## Lesson Learned

- `secret "X" not found` → check the **reference** (`helm get values`, the Pod spec) and the **object**
  (`kubectl get secret`); one of them is wrong.
- Existing-Secret patterns move responsibility outside the chart: document which Secrets must exist, with which
  keys, before an install. A `required` check or a pre-install hook can stop the install early, but cannot create the
  password for you.
- A Secret's value matters as much as its existence: credentials for stateful systems must match what the system
  was initialised with.
- Never debug secrets by printing them into logs or tickets. Compare them by hash if you must:
  `... | base64 -d | sha256sum`.
