# 06 · Failed upgrade

> Uses demo-app in namespace `trouble`. Time: 15 minutes.

## Break it

A working release:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install demo charts/demo-app --namespace trouble --create-namespace \
  -f troubleshooting/values-trouble.yaml --wait --timeout 3m | grep STATUS
```

A security hardening ticket: "applications must run under the service account the platform team manages,
`bookshop-runtime`, not one their chart creates". The chart supports it (`serviceAccount.create`, `serviceAccount.name`):

<!-- test: fail; timeout=300; contains=UPGRADE FAILED; output -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml \
  --set serviceAccount.create=false --set serviceAccount.name=bookshop-runtime \
  --wait --timeout 60s
```

```text
level=WARN msg="upgrade failed" name=demo error="resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Updated: 0/1\ncontext deadline exceeded"
Error: UPGRADE FAILED: resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Updated: 0/1
context deadline exceeded
```

## Problem

The upgrade fails after 60 seconds: the Deployment never becomes ready.

## Symptoms

<!-- test: contains=failed; output -->
```bash
helm status demo --namespace trouble | grep -E '^(STATUS|REVISION):'
helm history demo --namespace trouble
```

```text
STATUS: failed
REVISION: 2
REVISION	UPDATED                 	STATUS  	CHART         	APP VERSION	DESCRIPTION                                                                                                          
1       	Mon Oct  5 02:06:25 2026	deployed	demo-app-1.0.0	1.0.0      	Install complete                                                                                                     
2       	Mon Oct  5 02:06:31 2026	failed  	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Updated: ...
```

<!-- test: retry=20; contains=APP_ENV: "dev"; output -->
```bash
curl -s http://trouble.localhost:8080/config.js; echo
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };
```

The application still answers: users are not affected yet.

## Investigation

Helm's error says the Deployment did not become ready in time; it does not say why. The rolling update creates new
Pods next to the old ones. So: what happened to the **new** Pods?

## Commands

<!-- test: contains=Running; output -->
```bash
kubectl get pods --namespace trouble
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
demo-demo-app-68d8b4d8dc-nfq97   1/1     Running   0          67s
```

One Pod, the old one. There is no new Pod at all: not failing, not pending, simply absent. When Pods are missing, the
question moves one level up, to the object that creates them: the ReplicaSet.

<!-- test: output -->
```bash
kubectl get deployment,replicasets --namespace trouble
```

```text
NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/demo-demo-app   1/1     0            1           67s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/demo-demo-app-68d8b4d8dc   1         1         1       67s
replicaset.apps/demo-demo-app-6dc8c7c7f5   1         0         0       61s
```

<!-- test: contains=bookshop-runtime; output -->
```bash
kubectl get events --namespace trouble --field-selector reason=FailedCreate \
  -o custom-columns='OBJECT:.involvedObject.name,MESSAGE:.message' | tail -2
```

```text
OBJECT                     MESSAGE
demo-demo-app-6dc8c7c7f5   Error creating: pods "demo-demo-app-6dc8c7c7f5-" is forbidden: error looking up service account trouble/bookshop-runtime: serviceaccount "bookshop-runtime" not found
```

## Output Interpretation

- The new ReplicaSet wants 1 Pod and has 0: it cannot create it. The Deployment waits for it, the old ReplicaSet keeps
  its Pod (that is why users were not affected), and Helm's `--wait` times out.
- The event says why: the service account `bookshop-runtime` does not exist. A Pod that refers to a missing service
  account is rejected by the API server when the ReplicaSet tries to create it.
- `helm status`: revision 2 `failed`. The release record is honest: it is not running revision 2.

## Root Cause

The upgrade referred to a service account that does not exist yet: the platform team had not created it. The values were
valid YAML and valid Kubernetes; only applying them showed what was missing. (Real-life variants of "no new Pod at all":
a missing PriorityClass, an exhausted ResourceQuota, an admission policy that rejects the Pod.)

## Fix

Two options: roll back to revision 1 (fastest, when you need the previous state now), or provide what is missing and
upgrade again. Here the account is the agreed target, so create it (in real life: the platform team does), then upgrade:

<!-- test: contains=created -->
```bash
kubectl create serviceaccount bookshop-runtime --namespace trouble
```

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml \
  --set serviceAccount.create=false --set serviceAccount.name=bookshop-runtime \
  --wait --timeout 3m | grep STATUS
```

## Verification

<!-- test: retry=30; contains=bookshop-runtime; absent=Terminating; output -->
```bash
kubectl get pods --namespace trouble
kubectl get deployment demo-demo-app --namespace trouble -o jsonpath='{.spec.template.spec.serviceAccountName}'; echo
helm history demo --namespace trouble | tail -2
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
demo-demo-app-6dc8c7c7f5-f2qbm   1/1     Running   0          8s
bookshop-runtime
2       	Mon Oct  5 02:06:31 2026	failed    	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Updated: ...
3       	Mon Oct  5 02:07:32 2026	deployed  	demo-app-1.0.0	1.0.0      	Upgrade complete                                                                                                     
```

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
kubectl delete serviceaccount bookshop-runtime --namespace trouble > /dev/null
```

## Lesson Learned

- A failed upgrade with `--wait` is the good case: Helm noticed, the old Pods kept serving, the history says `failed`.
- Read Helm's error, then ask Kubernetes about the **new** Pods. No new Pod at all → look one level up: the
  ReplicaSet and its `FailedCreate` events.
- A chart value can point at something the chart does not create (a service account, a Secret, a StorageClass). Those
  are agreements with whoever creates them; check they exist before you upgrade.
- Decide between rollback (restore now) and fix-forward (provide what is missing) consciously; both end in a
  `deployed` revision.
