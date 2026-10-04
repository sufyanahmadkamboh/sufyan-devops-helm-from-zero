# Lab 09 · Rollback

> Level 11. Time: 40 minutes. The most important lab of the release-management part.

## Objective

Deploy a bad version on purpose, investigate it, and roll back to a known-good revision. Then let Helm do it
automatically, and recover a release that is stuck in the middle of an upgrade.

> Helm rollback is one of the important reasons release history matters.

## Prerequisites

- [Lab 08](08-upgrade.md).

## Task

In a fresh namespace `demo-rollback`:

1. Revision 1: install. Revision 2: a good change (an admin link).
2. Revision 3: a bad upgrade (an image tag that does not exist). Investigate.
3. Roll back to revision 2 and prove the application is healthy.
4. Repeat the bad upgrade with automatic rollback.

## Commands

### 1 · Two good revisions

The dev values, with the host changed so this release does not collide with lab 08's `demo-dev.localhost`:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install demo charts/demo-app --namespace demo-rollback --create-namespace \
  -f charts/demo-app/values-dev.yaml --set 'ingress.hosts[0].host=demo-rollback.localhost' \
  --wait --timeout 3m | grep -E 'STATUS|REVISION'
```

<!-- test: timeout=300; contains=REVISION: 2 -->
```bash
helm upgrade demo charts/demo-app --namespace demo-rollback \
  -f charts/demo-app/values-dev.yaml --set 'ingress.hosts[0].host=demo-rollback.localhost' \
  --set config.adminUrl=http://admin.example.com \
  --wait --timeout 3m | grep -E 'STATUS|REVISION'
```

<!-- test: retry=20; contains=admin.example.com; output -->
```bash
curl -s http://demo-rollback.localhost:8080/config.js; echo
```

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin.example.com", APP_ENV: "dev" };
```

Revision 2 is our known-good state.

### 2 · A bad upgrade

Someone deploys an image tag that was never published:

<!-- test: fail; timeout=300; contains=UPGRADE FAILED; output -->
```bash
helm upgrade demo charts/demo-app --namespace demo-rollback \
  -f charts/demo-app/values-dev.yaml --set 'ingress.hosts[0].host=demo-rollback.localhost' \
  --set config.adminUrl=http://admin.example.com \
  --set image.tag=1.0.1-hotfix \
  --wait --timeout 60s
```

```text
level=WARN msg="upgrade failed" name=demo error="resource Deployment/demo-rollback/demo-demo-app not ready. status: InProgress, message: Pending termination: 1\ncontext deadline exceeded"
Error: UPGRADE FAILED: resource Deployment/demo-rollback/demo-demo-app not ready. status: InProgress, message: Pending termination: 1
context deadline exceeded
```

With `--wait`, Helm watched the Deployment for 60 seconds, it never became ready, and Helm marked the revision
`failed`. Without `--wait`, Helm would have reported success: it only knows what it waits for.

### 3 · Investigate

This is where Helm history becomes useful:

<!-- test: contains=failed; output -->
```bash
helm history demo --namespace demo-rollback
```

```text
REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION                                                                                                                          
1       	Sun Oct  4 23:37:31 2026	superseded	demo-app-1.0.0	1.0.0      	Install complete                                                                                                                     
2       	Sun Oct  4 23:37:32 2026	deployed  	demo-app-1.0.0	1.0.0      	Upgrade complete                                                                                                                     
3       	Sun Oct  4 23:37:36 2026	failed    	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: resource Deployment/demo-rollback/demo-demo-app not ready. status: InProgress, message: Pending termination...
```

The Kubernetes side:

<!-- test: contains=ImagePull; output -->
```bash
kubectl get pods --namespace demo-rollback
```

```text
NAME                             READY   STATUS         RESTARTS   AGE
demo-demo-app-56457858d8-ht7np   1/1     Running        0          64s
demo-demo-app-6dc6b54f46-lpc2j   0/1     ErrImagePull   0          60s
```

<!-- test: contains=1.0.1-hotfix; output -->
```bash
kubectl describe pods --namespace demo-rollback -l app.kubernetes.io/instance=demo | grep -E 'Image:|Failed|not found' | sort -u | head -6
```

```text
    Image:          ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0
    Image:          ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.1-hotfix
```

The new Pod cannot pull `bookshop-frontend:1.0.1-hotfix`: the tag does not exist. And the application?

<!-- test: retry=5; contains=admin.example.com; output -->
```bash
curl -s http://demo-rollback.localhost:8080/config.js; echo
```

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin.example.com", APP_ENV: "dev" };
```

Still up. The rolling update creates the new Pod **before** removing an old one, and never removes an old Pod
until a new one is Ready. The failed upgrade is stuck half-way, with the old Pod still serving: Kubernetes protected
you, but the release is in a failed state and nobody should leave it like this.

### 4 · Roll back

Back to the last good revision, 2:

<!-- test: timeout=300; contains=Rollback was a success; output -->
```bash
helm rollback demo 2 --namespace demo-rollback --wait --timeout 3m
```

```text
Rollback was a success! Happy Helming!
```

<!-- test: contains=Rollback to 2; output -->
```bash
helm history demo --namespace demo-rollback
helm status demo --namespace demo-rollback | grep -E '^(STATUS|REVISION):'
```

```text
REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION                                                                                                                          
1       	Sun Oct  4 23:37:31 2026	superseded	demo-app-1.0.0	1.0.0      	Install complete                                                                                                                     
2       	Sun Oct  4 23:37:32 2026	superseded	demo-app-1.0.0	1.0.0      	Upgrade complete                                                                                                                     
3       	Sun Oct  4 23:37:36 2026	failed    	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: resource Deployment/demo-rollback/demo-demo-app not ready. status: InProgress, message: Pending termination...
4       	Sun Oct  4 23:38:37 2026	deployed  	demo-app-1.0.0	1.0.0      	Rollback to 2                                                                                                                        
STATUS: deployed
REVISION: 4
```

A rollback does not delete revision 3 or rewind the counter: it creates **revision 4**, a copy of revision 2's
manifest and values. History only grows, so the record shows exactly what happened, including the failure.

<!-- test: retry=30; contains=successfully rolled out; absent=ImagePull; absent=Terminating; output -->
```bash
kubectl rollout status deployment/demo-demo-app --namespace demo-rollback
kubectl get pods --namespace demo-rollback
curl -s http://demo-rollback.localhost:8080/config.js; echo
```

```text
deployment "demo-demo-app" successfully rolled out
NAME                             READY   STATUS    RESTARTS   AGE
demo-demo-app-56457858d8-ht7np   1/1     Running   0          68s
window.APP_CONFIG = { ADMIN_URL: "http://admin.example.com", APP_ENV: "dev" };
```

The broken Pod is gone, the admin link (from revision 2) is still there.

### 5 · Automatic rollback

`--rollback-on-failure` (Helm 3 called it `--atomic`) does steps 3–4 for you: if the upgrade fails, Helm rolls back
to the previous revision immediately.

<!-- test: fail; timeout=300; contains=has been rolled back; output=tail:2 -->
```bash
helm upgrade demo charts/demo-app --namespace demo-rollback \
  -f charts/demo-app/values-dev.yaml --set 'ingress.hosts[0].host=demo-rollback.localhost' \
  --set config.adminUrl=http://admin.example.com \
  --set image.tag=1.0.1-hotfix \
  --rollback-on-failure --timeout 60s
```

```text
...
Error: UPGRADE FAILED: release demo failed, and has been rolled back due to rollback-on-failure being set: resource Deployment/demo-rollback/demo-demo-app not ready. status: InProgress, message: Pending termination: 1
context deadline exceeded
```

<!-- test: contains=Rollback to 4; output -->
```bash
helm history demo --namespace demo-rollback
```

```text
REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION                                                                                                                          
1       	Sun Oct  4 23:37:31 2026	superseded	demo-app-1.0.0	1.0.0      	Install complete                                                                                                                     
2       	Sun Oct  4 23:37:32 2026	superseded	demo-app-1.0.0	1.0.0      	Upgrade complete                                                                                                                     
3       	Sun Oct  4 23:37:36 2026	failed    	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: resource Deployment/demo-rollback/demo-demo-app not ready. status: InProgress, message: Pending termination...
4       	Sun Oct  4 23:38:37 2026	superseded	demo-app-1.0.0	1.0.0      	Rollback to 2                                                                                                                        
5       	Sun Oct  4 23:38:41 2026	failed    	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: resource Deployment/demo-rollback/demo-demo-app not ready. status: InProgress, message: Pending termination...
6       	Sun Oct  4 23:39:41 2026	deployed  	demo-app-1.0.0	1.0.0      	Rollback to 4                                                                                                                        
```

## Expected Output

- Revision 3 `failed`, Pods in `ErrImagePull`/`ImagePullBackOff`, the old Pod still serving.
- `Rollback was a success! Happy Helming!`, revision 4 `deployed` `Rollback to 2`.
- With `--rollback-on-failure`: revision 5 `failed`, revision 6 `deployed` `Rollback to 4`.

## Explanation

```text
 rev 1  install          superseded
 rev 2  admin link       superseded   ◄── known good
 rev 3  bad image tag    failed
 rev 4  rollback to 2    superseded   (a copy of rev 2)
 rev 5  bad image again  failed       (--rollback-on-failure)
 rev 6  rollback to 4    deployed
```

What a rollback restores: the Kubernetes objects of the target revision (manifest + values). What it does **not**
restore: data. A database migration run by the bad version, files written to a volume, messages already sent: all
stay. Rollback is a deployment tool, not a time machine; that is why risky data changes need their own plan
(backups, backwards-compatible migrations).

Kubernetes has its own `kubectl rollout undo` for a single Deployment. Prefer `helm rollback` for Helm-managed
applications: it restores every object of the release together (ConfigMap, Service, Ingress ...), and keeps Helm's
record in sync with the cluster.

## Break It

An upgrade interrupted half-way (a CI job cancelled, a laptop closed, a network drop). `timeout 5` kills Helm after
5 seconds, in the middle of its `--wait`:

<!-- test: fail; timeout=120; output -->
```bash
timeout 5 helm upgrade demo charts/demo-app --namespace demo-rollback \
  -f charts/demo-app/values-dev.yaml --set 'ingress.hosts[0].host=demo-rollback.localhost' \
  --set image.tag=1.0.1-hotfix --wait --timeout 5m
```

```text
```

No output: `timeout` stopped Helm (exit code 124) while it was waiting. Now try any normal upgrade:

<!-- test: fail; contains=another operation (install/upgrade/rollback) is in progress; output -->
```bash
helm upgrade demo charts/demo-app --namespace demo-rollback \
  -f charts/demo-app/values-dev.yaml --set 'ingress.hosts[0].host=demo-rollback.localhost'
```

```text
Error: UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress
```

## Troubleshoot It

Nothing is in progress: the process that started the operation is dead. But Helm writes the revision record as
`pending-upgrade` **before** applying, and only the process that started it could have completed it:

<!-- test: contains=pending-upgrade; output -->
```bash
helm history demo --namespace demo-rollback | tail -2
```

```text
6       	Sun Oct  4 23:39:41 2026	deployed       	demo-app-1.0.0	1.0.0      	Rollback to 4                                                                                                                        
7       	Sun Oct  4 23:39:41 2026	pending-upgrade	demo-app-1.0.0	1.0.0      	Preparing upgrade                                                                                                                    
```

Helm refuses to start a second operation on a release with a pending one; that lock protects you from two pipelines
deploying at once. The way out is a rollback to the last good revision, which replaces the pending state:

<!-- test: timeout=300; contains=Rollback was a success -->
```bash
helm rollback demo 6 --namespace demo-rollback --wait --timeout 3m
```

<!-- test: contains=Rollback to 6; output -->
```bash
helm history demo --namespace demo-rollback | tail -3
```

```text
6       	Sun Oct  4 23:39:41 2026	superseded     	demo-app-1.0.0	1.0.0      	Rollback to 4                                                                                                                        
7       	Sun Oct  4 23:39:41 2026	pending-upgrade	demo-app-1.0.0	1.0.0      	Preparing upgrade                                                                                                                    
8       	Sun Oct  4 23:39:47 2026	deployed       	demo-app-1.0.0	1.0.0      	Rollback to 6                                                                                                                        
```

(Revision 7 stays `pending-upgrade` in the history: a record of what happened, no longer a lock.) Before you do this
in production, make sure the operation really is dead: check the CI job, ask your team.

## Challenge

Without looking at `helm history` output by eye, find the **values** that were in effect in revision 2 and the
image tag that revision 5 tried to deploy, using `helm get`.

## Solution

<details>
<summary>Open the solution</summary>

Every `helm get` subcommand takes `--revision`:

<!-- test: contains=admin.example.com; contains=1.0.1-hotfix; output -->
```bash
helm get values demo --namespace demo-rollback --revision 2
helm get manifest demo --namespace demo-rollback --revision 5 | grep 'image:'
```

```text
USER-SUPPLIED VALUES:
config:
  adminUrl: http://admin.example.com
environment: dev
ingress:
  enabled: true
  hosts:
  - host: demo-rollback.localhost
    paths:
    - path: /
      pathType: Prefix
replicaCount: 1
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.1-hotfix"
```

`helm get manifest --revision N` is how you answer "what exactly was deployed on Tuesday?", even when the chart
folder has changed since.

</details>

## Verification

<!-- test: retry=20; contains=deployed; contains=APP_ENV: "dev"; output -->
```bash
helm status demo --namespace demo-rollback | grep '^STATUS:'
curl -s http://demo-rollback.localhost:8080/config.js; echo
```

```text
STATUS: deployed
window.APP_CONFIG = { ADMIN_URL: "http://admin.example.com", APP_ENV: "dev" };
```

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls the release demo in demo-rollback and deletes the namespace.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall demo --namespace demo-rollback --wait
kubectl delete namespace demo-rollback --wait=false
```

Next: [lab 10 · Environments](10-environments.md).
