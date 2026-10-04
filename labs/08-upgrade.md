# Lab 08 · Upgrade a release

> Level 10. Time: 35 minutes.

## Objective

Change a running release: review the change before applying it, upgrade, follow the rolling update on the
Kubernetes side, and read the release history. Learn the most common upgrade mistake: forgetting values.

## Prerequisites

- [Lab 07](07-install-release.md): release `demo` in namespace `demo-dev`.

## Task

1. Plan an upgrade: 2 replicas and an admin link in the configuration.
2. Show what will change **before** upgrading.
3. Upgrade, watch the rollout, check history and values per revision.

## Commands

### 1 · Review before you upgrade

What will this upgrade change in the cluster? Render the new state and let `kubectl diff` compare it with the live
objects. The API server computes the result of applying it, the way Helm 4 applies (server-side apply, as field
manager `helm`), and changes nothing:

<!-- test: contains=+  replicas: 2; contains=ADMIN_URL; output -->
```bash
helm template demo charts/demo-app --namespace demo-dev --skip-tests \
  -f charts/demo-app/values-dev.yaml \
  --set replicaCount=2 --set config.adminUrl=http://admin.example.com \
  | kubectl diff --server-side --field-manager=helm --namespace demo-dev -f - \
  | grep -E '^[-+] ' | grep -vE 'generation:|meta\.helm\.sh/|^-\s+annotations:$' || true
```

```text
-  replicas: 1
+  replicas: 2
-        checksum/config: 54958286d0b76d4d3f56e865ba7aac664ce6a00a2b1c2c37a9705fb86455ce26
+        checksum/config: dfb19afd95348e60cfd144eac490e1274279b4fc17370b8d5649585ebb8c5f07
-  ADMIN_URL: ""
+  ADMIN_URL: http://admin.example.com
```

Three changes: replicas `1 → 2`, the ConfigMap's `ADMIN_URL`, and the `checksum/config` annotation of the Pod
template (because the ConfigMap changed). The checksum means: the Pods will be replaced, so they pick up the new
configuration.

The pipeline, piece by piece:

| Part | Why |
|---|---|
| `--skip-tests` | leave out the test Pod: it only exists while `helm test` runs |
| `--server-side --field-manager=helm` | compute the result the way Helm 4 applies it (a client-side diff can report errors Helm would not hit, for example when a Service port changes) |
| `grep -E '^[-+] '` | keep only the changed lines |
| `grep -vE 'generation:\|meta.helm.sh/\|...'` | drop noise: Helm adds its ownership annotations at install time (they are not in the templates), and `generation` always increases |
| `\|\| true` | `kubectl diff` exits with 1 when there are differences |

> Many teams use the [helm-diff plugin](https://github.com/databus23/helm-diff) for the same purpose
> (`helm diff upgrade demo charts/demo-app -f ...`). It is optional: the `helm template | kubectl diff` pipeline
> above needs nothing but the tools you have. If you install the plugin, pin its version and read what it does first:
> plugins run with your credentials. Helm 4 verifies plugin signatures; a plugin installed from a Git URL has none, so
> Helm refuses it unless you pass `--verify=false` (a conscious decision to trust that source). On Windows, the
> plugin's install script needs PowerShell 7 (`pwsh`).

<!-- test: skip -->
```bash
helm plugin install https://github.com/databus23/helm-diff --version v3.15.15 --verify=false
helm diff upgrade demo charts/demo-app -n demo-dev -f charts/demo-app/values-dev.yaml --set replicaCount=2
```

### 2 · Upgrade

<!-- test: timeout=300; contains=STATUS: deployed; output=head:6 -->
```bash
helm upgrade demo charts/demo-app --namespace demo-dev \
  -f charts/demo-app/values-dev.yaml \
  --set replicaCount=2 --set config.adminUrl=http://admin.example.com \
  --wait --timeout 3m
```

```text
Release "demo" has been upgraded. Happy Helming!
NAME: demo
LAST DEPLOYED: Mon Oct  5 01:00:03 2026
NAMESPACE: demo-dev
STATUS: deployed
REVISION: 3
...
```

### 3 · The Kubernetes side

```text
helm upgrade ─► Deployment updated ─► new ReplicaSet ─► new Pods (Ready) ─► old Pods removed
                (new Pod template)     (rolling update: maxSurge 25 %, maxUnavailable 25 %)
```

<!-- test: contains=successfully rolled out; output -->
```bash
kubectl rollout status deployment/demo-demo-app --namespace demo-dev
kubectl rollout history deployment/demo-demo-app --namespace demo-dev
```

```text
deployment "demo-demo-app" successfully rolled out
deployment.apps/demo-demo-app 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

Two Deployment revisions: the original Pod template and the one with the new checksum. These are **Kubernetes**
revisions (ReplicaSets), not Helm revisions: Helm manages the release, Kubernetes manages the rollout.

<!-- test: retry=20; contains=admin.example.com; absent=Terminating; absent=Completed; output -->
```bash
kubectl get pods --namespace demo-dev -l app.kubernetes.io/instance=demo
curl -s http://demo-dev.localhost:8080/config.js; echo
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
demo-demo-app-56457858d8-2l24x   1/1     Running   0          4s
demo-demo-app-56457858d8-cl459   1/1     Running   0          5s
window.APP_CONFIG = { ADMIN_URL: "http://admin.example.com", APP_ENV: "dev" };
```

### 4 · The Helm side

<!-- test: contains=Upgrade complete; output -->
```bash
helm history demo --namespace demo-dev
```

```text
REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION     
1       	Mon Oct  5 00:59:39 2026	superseded	demo-app-1.0.0	1.0.0      	Install complete
2       	Mon Oct  5 00:59:57 2026	superseded	demo-app-1.0.0	1.0.0      	Upgrade complete
3       	Mon Oct  5 01:00:03 2026	deployed  	demo-app-1.0.0	1.0.0      	Upgrade complete
```

Each line is a revision: when, which chart and app version, its status. The values of any revision are kept:

<!-- test: contains=replicaCount: 2; contains=admin.example.com; output -->
```bash
helm get values demo --namespace demo-dev --revision 1
echo ---
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
---
USER-SUPPLIED VALUES:
config:
  adminUrl: http://admin.example.com
environment: dev
ingress:
  enabled: true
  hosts:
  - host: demo-dev.localhost
    paths:
    - path: /
      pathType: Prefix
replicaCount: 2
```

## Expected Output

- The diff shows exactly three changed lines groups: replicas, the ConfigMap value, the checksum.
- Two Pods, `config.js` with `ADMIN_URL: "http://admin.example.com"`.
- `helm history`: revisions 1 (install), 2 (the no-op upgrade of lab 07), 3 (this upgrade).

## Explanation

`helm upgrade` renders the chart with the values **you give in this command**, compares the result with the
previous revision's manifest and the live objects, and applies the difference (Helm 4: server-side apply). Objects
that disappeared from the rendered output are deleted. A new revision is stored; the previous one becomes
`superseded`.

That first sentence is the trap of the next section.

## Break It

A colleague just wants 3 replicas, quickly:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace demo-dev --set replicaCount=3 --wait | grep STATUS
```

<!-- test: retry=10; contains=404 page not found; output -->
```bash
curl -s http://demo-dev.localhost:8080/config.js; echo
```

```text
404 page not found
```

The upgrade "succeeded", and the application is gone from its address.

## Troubleshoot It

Let's investigate this like we would in production: what changed between the last two revisions?

<!-- test: contains=replicaCount: 3; absent=demo-dev.localhost; output -->
```bash
helm history demo --namespace demo-dev | tail -2
helm get values demo --namespace demo-dev
```

```text
3       	Mon Oct  5 01:00:03 2026	superseded	demo-app-1.0.0	1.0.0      	Upgrade complete
4       	Mon Oct  5 01:00:09 2026	deployed  	demo-app-1.0.0	1.0.0      	Upgrade complete
USER-SUPPLIED VALUES:
replicaCount: 3
```

The latest revision's user-supplied values are only `replicaCount: 3`. The dev file was not passed, so the release
fell back to the chart defaults: `ingress.enabled: false` (Ingress deleted), `environment: local`, no admin link.

<!-- test: contains=local; output -->
```bash
kubectl get ingress --namespace demo-dev 2>&1
kubectl get configmap demo-demo-app --namespace demo-dev -o jsonpath='{.data.APP_ENV}'; echo
```

```text
No resources found in demo-dev namespace.
local
```

**Root cause:** `helm upgrade` does not remember previous values unless asked (`--reuse-values`), and asking is its
own trap: it would also keep stale values forever and ignore new defaults of a new chart version. **Fix:** always
pass the complete set of values files, the same way every time; better, from a script or pipeline:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace demo-dev \
  -f charts/demo-app/values-dev.yaml --set replicaCount=3 --wait | grep STATUS
```

<!-- test: retry=20; contains=APP_ENV: "dev" -->
```bash
curl -s http://demo-dev.localhost:8080/config.js; echo
```

**Lesson:** the values files are part of the deployment command. Keep the exact command in a script or CI job,
not in someone's memory.

## Challenge

Change the **Service** configuration: the Service must listen on port **80** while the container keeps listening on
8080. Review the change with a diff first, then upgrade, and prove the Ingress still reaches the application.

## Solution

<details>
<summary>Open the solution</summary>

The chart separates `service.port` (the Service) from `containerPort` (the container), and the Service's `targetPort`
is the named port `http`. The Ingress template uses `service.port`, so it follows:

<!-- test: contains=port: 80; output -->
```bash
helm template demo charts/demo-app --namespace demo-dev --skip-tests -f charts/demo-app/values-dev.yaml \
  --set replicaCount=3 --set service.port=80 \
  | kubectl diff --server-side --field-manager=helm --namespace demo-dev -f - \
  | grep -E '^[-+] ' | grep -vE 'generation:|meta\.helm\.sh/|^-\s+annotations:$' || true
```

```text
-              number: 8080
+              number: 80
-    port: 8080
+    port: 80
```

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace demo-dev -f charts/demo-app/values-dev.yaml \
  --set replicaCount=3 --set service.port=80 --wait | grep STATUS
```

</details>

## Verification

<!-- test: retry=20; contains=80/TCP; contains=APP_ENV: "dev"; output -->
```bash
kubectl get service demo-demo-app --namespace demo-dev
curl -s http://demo-dev.localhost:8080/config.js; echo
```

```text
NAME            TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
demo-demo-app   ClusterIP   10.96.82.185   <none>        80/TCP    76s
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };
```

## Cleanup

Back to the plain dev configuration (the next lab starts from here):

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace demo-dev -f charts/demo-app/values-dev.yaml --wait | grep STATUS
```

Next: [lab 09 · Rollback](09-rollback.md).
