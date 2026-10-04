# 06 · Failed upgrade

> Uses demo-app in namespace `trouble`. Time: 15 minutes.

## Break it

A working release:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install demo charts/demo-app --namespace trouble --create-namespace \
  -f troubleshooting/values-trouble.yaml --wait --timeout 3m | grep STATUS
```

A cost-saving initiative: "the frontend uses almost no memory, set its limit to 6 MiB":

<!-- test: fail; timeout=300; contains=UPGRADE FAILED; output -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml \
  --set resources.requests.memory=6Mi --set resources.limits.memory=6Mi \
  --wait --timeout 60s
```

```text
level=WARN msg="upgrade failed" name=demo error="resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Pending termination: 1\ncontext deadline exceeded"
Error: UPGRADE FAILED: resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Pending termination: 1
context deadline exceeded
```

## Problem

The upgrade fails after 60 seconds with `not ready ... context deadline exceeded`.

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
1       	Mon Oct  5 01:08:35 2026	deployed	demo-app-1.0.0	1.0.0      	Install complete                                                                                                               
2       	Mon Oct  5 01:08:37 2026	failed  	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Pending termination...
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

<!-- test: contains=CrashLoopBackOff; output -->
```bash
kubectl get pods --namespace trouble
```

```text
NAME                             READY   STATUS             RESTARTS      AGE
demo-demo-app-5965f57d7f-4n4zj   0/1     CrashLoopBackOff   3 (21s ago)   60s
demo-demo-app-68d8b4d8dc-f5fjt   1/1     Running            0             62s
```

<!-- test: contains=OOMKilled; output -->
```bash
kubectl describe pod --namespace trouble -l app.kubernetes.io/instance=demo | grep -E 'Limits:|memory:|Reason|Exit Code' | head -8
```

```text
      Reason:       CrashLoopBackOff
      Reason:       OOMKilled
      Exit Code:    137
    Limits:
      memory:  6Mi
      memory:   6Mi
    Limits:
      memory:  128Mi
```

<!-- test: contains=BackOff; output -->
```bash
kubectl get events --namespace trouble --sort-by=.lastTimestamp | tail -6
```

```text
61s         Normal    ScalingReplicaSet   deployment/demo-demo-app              Scaled up replica set demo-demo-app-5965f57d7f from 0 to 1
23s         Normal    Pulled              pod/demo-demo-app-5965f57d7f-4n4zj    Container image "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0" already present on machine and can be accessed by the pod
23s         Normal    Created             pod/demo-demo-app-5965f57d7f-4n4zj    Container created
23s         Normal    Started             pod/demo-demo-app-5965f57d7f-4n4zj    Container started
23s         Warning   Unhealthy           pod/demo-demo-app-5965f57d7f-4n4zj    Readiness probe failed: Get "http://10.244.1.104:8080/health": dial tcp 10.244.1.104:8080: connect: connection refused
21s         Warning   BackOff             pod/demo-demo-app-5965f57d7f-4n4zj    Back-off restarting failed container demo-app in pod demo-demo-app-5965f57d7f-4n4zj_trouble(97871a35-bfda-4fac-9f6d-54464c33253c)
```

## Output Interpretation

- Two Pods: the old one (`1/1 Running`, still serving) and the new one in `CrashLoopBackOff`. Kubernetes never
  removes an old Pod until a new one is Ready, which is why users were not affected.
- `Reason: OOMKilled`, `Exit Code: 137`: the kernel killed the container because it used more memory than its
  6 MiB limit. nginx and its worker processes need more than that just to start.
- `helm status`: revision 2 `failed`. The release record is honest: it is not running revision 2.

## Root Cause

A memory limit below what the application needs to start. The value was valid YAML and valid Kubernetes; only
running it showed it was wrong. (Real-life variants: a too-low limit that only fails under load, a CPU limit that
makes startup exceed the liveness probe's patience.)

## Fix

Two options: roll back to revision 1 (fastest, when you need the previous state now), or fix the value and upgrade
(when you know the right number). Measure first, then set the limit with headroom:

<!-- test: contains=MEMORY; output -->
```bash
kubectl top pod --namespace trouble 2>/dev/null || echo "MEMORY: no metrics-server in kind; in a real cluster, measure with kubectl top or your monitoring"
```

```text
MEMORY: no metrics-server in kind; in a real cluster, measure with kubectl top or your monitoring
```

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml \
  --set resources.requests.memory=32Mi --set resources.limits.memory=96Mi \
  --wait --timeout 3m | grep STATUS
```

## Verification

<!-- test: retry=30; contains=96Mi; absent=CrashLoopBackOff; absent=Terminating; output -->
```bash
kubectl get pods --namespace trouble
kubectl get deployment demo-demo-app --namespace trouble -o jsonpath='{.spec.template.spec.containers[0].resources}'; echo
helm history demo --namespace trouble | tail -2
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
demo-demo-app-67df7fc4f5-xng57   1/1     Running   0          4s
{"limits":{"cpu":"200m","memory":"96Mi"},"requests":{"cpu":"10m","memory":"32Mi"}}
2       	Mon Oct  5 01:08:37 2026	failed    	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Pending termination...
3       	Mon Oct  5 01:09:39 2026	deployed  	demo-app-1.0.0	1.0.0      	Upgrade complete                                                                                                               
```

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
```

## Lesson Learned

- A failed upgrade with `--wait` is the good case: Helm noticed, the old Pods kept serving, the history says `failed`.
- Read Helm's error, then ask Kubernetes about the **new** Pods: `get pods`, `describe` (reason, exit code), events.
- `OOMKilled` / exit 137 = memory limit too low (or a leak). Limits come from measurements, not guesses.
- Decide between rollback (restore now) and fix-forward (correct the value) consciously; both end in a `deployed`
  revision.
