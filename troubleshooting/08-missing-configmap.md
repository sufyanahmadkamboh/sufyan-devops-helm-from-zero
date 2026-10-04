# 08 · Missing ConfigMap

> Uses the `shop` release in `bookshop-dev` ([lab 12](../labs/12-dependencies.md)). Time: 15 minutes.

## Break it

While cleaning up "old" ConfigMaps by hand, someone deletes the Bookshop's:

<!-- test: contains=deleted -->
```bash
kubectl delete configmap shop-config --namespace bookshop-dev
```

Nothing happens. Later, the node-api Pod is restarted (a node drain, a crash, a new rollout):

<!-- test: contains=restarted -->
```bash
kubectl rollout restart deployment/shop-node-api --namespace bookshop-dev
```

## Problem

The users panel of the Bookshop keeps working for a while, then node-api's rollout never finishes.

## Symptoms

<!-- test: retry=20; contains=CreateContainerConfigError; output -->
```bash
kubectl get pods --namespace bookshop-dev -l app.kubernetes.io/name=node-api
```

```text
NAME                             READY   STATUS                       RESTARTS   AGE
shop-node-api-5c688d66c6-s8xbm   1/1     Running                      0          30s
shop-node-api-7b995d94bd-qhhss   0/1     CreateContainerConfigError   0          2s
```

## Investigation

`CreateContainerConfigError`: the container cannot even be created, because something its configuration refers to is
missing. The image is fine and the application never ran. The Pod's events say what is missing.

## Commands

<!-- test: retry=10; contains=configmap "shop-config" not found; output -->
```bash
kubectl get events --namespace bookshop-dev --field-selector reason=Failed \
  -o custom-columns='POD:.involvedObject.name,MESSAGE:.message' | grep node-api | grep configmap | tail -2
```

```text
shop-node-api-7b995d94bd-qhhss   Error: configmap "shop-config" not found
shop-node-api-97dc495b7-27kg9    Error: configmap "shop-config" not found
```

Is that ConfigMap supposed to exist? The release's manifest says yes:

<!-- test: contains=name: shop-config; output -->
```bash
helm get manifest shop --namespace bookshop-dev | grep -A3 '^kind: ConfigMap'
kubectl get configmap shop-config --namespace bookshop-dev 2>&1 || true
```

```text
kind: ConfigMap
metadata:
  name: shop-config
  labels:
Error from server (NotFound): configmaps "shop-config" not found
```

## Output Interpretation

- The new Pod refers to `shop-config` (`envFrom`), which does not exist: `configmap "shop-config" not found`.
- The old Pods kept running because environment variables are read once, at container start. A missing ConfigMap
  only hurts at the next start: often hours later, far from the deletion that caused it.
- Helm's record (`helm get manifest`) still contains the ConfigMap. Helm does not watch the cluster, so `helm status`
  shows `deployed` the whole time.

## Root Cause

A release-owned object was deleted outside Helm. The release is no longer complete.

## Fix

Re-apply the release: an upgrade with the same chart and values re-creates whatever is missing.

<!-- test: timeout=600; contains=STATUS: deployed -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-dev -f charts/bookshop/values-dev.yaml --wait --timeout 5m | grep STATUS
```

## Verification

<!-- test: retry=30; contains=shop-config; absent=CreateContainerConfigError; output -->
```bash
kubectl get configmap shop-config --namespace bookshop-dev
kubectl get pods --namespace bookshop-dev -l app.kubernetes.io/name=node-api
```

```text
NAME          DATA   AGE
shop-config   9      15s
NAME                             READY   STATUS    RESTARTS   AGE
shop-node-api-7b995d94bd-qhhss   1/1     Running   0          18s
```

<!-- test: timeout=300; contains=all checks passed -->
```bash
helm test shop --namespace bookshop-dev --logs | tail -2
```

## Lesson Learned

- `CreateContainerConfigError` = a referenced ConfigMap, Secret or key is missing; `kubectl describe pod` names it.
- Deleting configuration does not break running Pods, it breaks the next restart: the cause and the symptom can be
  hours apart.
- Compare the release with the cluster when something "disappeared": `helm get manifest` lists what should exist.
- Objects managed by Helm are changed through Helm. To find who deletes things, audit logs; to prevent it, RBAC
  (people do not need `delete configmaps` in application namespaces).
