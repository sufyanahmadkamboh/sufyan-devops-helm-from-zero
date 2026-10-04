# 02 · Wrong value

> Uses demo-app in namespace `trouble`. Time: 15 minutes.

## Break it

A colleague prepares values for a new environment and, "because web servers listen on 80", sets the container port:

<!-- test: contains=containerPort: 80 -->
```bash
mkdir -p labs/work
cat > labs/work/ts02-values.yaml <<'EOF'
containerPort: 80
EOF
cat labs/work/ts02-values.yaml
```

<!-- test: fail; timeout=300; contains=INSTALLATION FAILED; output -->
```bash
helm install demo charts/demo-app --namespace trouble --create-namespace \
  -f troubleshooting/values-trouble.yaml -f labs/work/ts02-values.yaml \
  --wait --timeout 60s
```

```text
Error: INSTALLATION FAILED: resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Available: 0/1
context deadline exceeded
```

## Problem

The install fails after 60 seconds: the Deployment never becomes available.

## Symptoms

<!-- test: contains=0/1; output -->
```bash
kubectl get pods --namespace trouble
```

```text
NAME                             READY   STATUS    RESTARTS      AGE
demo-demo-app-7fcd775c55-89hsc   0/1     Running   1 (30s ago)   60s
```

The Pod is `Running` but `0/1` (not Ready), and it keeps restarting.

## Investigation

Helm only reports that the Deployment never became ready; Kubernetes knows why. Two questions in order: what does
Kubernetes say about the Pod, and which of **our** inputs produced that?

## Commands

<!-- test: contains=connection refused; output -->
```bash
kubectl describe pod --namespace trouble -l app.kubernetes.io/instance=demo | grep -E 'Port:|Liveness|Readiness|Unhealthy' | head -6
```

```text
    Port:           80/TCP (http)
    Host Port:      0/TCP (http)
    Liveness:   http-get http://:http/health delay=0s timeout=1s period=10s successThreshold=1 failureThreshold=3
    Readiness:  http-get http://:http/health delay=0s timeout=1s period=5s successThreshold=1 failureThreshold=3
  Warning  Unhealthy  0s (x16 over 60s)  kubelet            spec.containers{demo-app}: Readiness probe failed: Get "http://10.244.1.94:80/health": dial tcp 10.244.1.94:80: connect: connection refused
  Warning  Unhealthy  0s (x6 over 50s)   kubelet            spec.containers{demo-app}: Liveness probe failed: Get "http://10.244.1.94:80/health": dial tcp 10.244.1.94:80: connect: connection refused
```

The probes call port 80, and nothing listens there. Where does 80 come from? Compare what was asked for with what Helm
applied:

<!-- test: contains=containerPort: 80; output -->
```bash
helm get values demo --namespace trouble
helm get manifest demo --namespace trouble | grep -nE 'containerPort|port: http|targetPort'
```

```text
USER-SUPPLIED VALUES:
containerPort: 80
environment: dev
ingress:
  enabled: true
  hosts:
  - host: trouble.localhost
    paths:
    - path: /
      pathType: Prefix
replicaCount: 1
54:      targetPort: http
112:              containerPort: 80
120:              port: http
125:              port: http
```

## Output Interpretation

- `Readiness probe failed: ... :80/health: connection refused`: the kubelet calls port 80 inside the Pod; nobody
  listens there, so the Pod is never Ready, and the liveness probe restarts it every 30 seconds.
- The probes don't say "80" in the chart: they use the **named** port `http` (`port: http`). `containerPort: 80`
  renamed what `http` means.
- `helm get values` shows the culprit: `containerPort: 80`, user-supplied.

## Root Cause

The chart's `containerPort` value is the port **the application listens on**, not a port you can choose: the
Bookshop frontend's nginx listens on 8080 (it runs as a non-root user, which cannot bind ports below 1024). Setting
it to 80 makes Kubernetes probe and route to a port nothing serves.

## Fix

Remove the wrong value: upgrade with the correct files only. (`--wait` again: we want to know it really works.)

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml --wait --timeout 3m | grep STATUS
```

## Verification

<!-- test: retry=20; contains=1/1; contains=APP_ENV: "dev"; absent=Terminating; output -->
```bash
kubectl get pods --namespace trouble
curl -s http://trouble.localhost:8080/config.js; echo
helm history demo --namespace trouble
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
demo-demo-app-68d8b4d8dc-nq6wl   1/1     Running   0          4s
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION                                                                                                            
1       	Mon Oct  5 01:06:51 2026	superseded	demo-app-1.0.0	1.0.0      	Release "demo" failed: resource Deployment/trouble/demo-demo-app not ready. status: InProgress, message: Available: ...
2       	Mon Oct  5 01:07:52 2026	deployed  	demo-app-1.0.0	1.0.0      	Upgrade complete                                                                                                       
```

Revision 2 `deployed`; revision 1 is now `superseded`, and its description still records the failed install. An
upgrade can repair a failed install, as long as the release exists.

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
rm -f labs/work/ts02-values.yaml
```

## Lesson Learned

- `Running 0/1` + restarts + `connection refused` in probe events = the application is not listening where Kubernetes
  is looking.
- `helm get values` (what was asked) and `helm get manifest` (what was applied) find which input caused it.
- Document what each value means, especially values that must match the application (ports, paths). A
  `values.schema.json` with `"enum": [8080]` or a `description` would have stopped this at install time
  ([lab 04](../labs/04-values.md)).
- Always install and upgrade with `--wait`: without it, this install would have reported `deployed`.
