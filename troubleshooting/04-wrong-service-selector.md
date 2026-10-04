# 04 · Wrong Service selector

> Uses demo-app in namespace `trouble`. Time: 15 minutes.

## Break it

A working release:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install demo charts/demo-app --namespace trouble --create-namespace \
  -f troubleshooting/values-trouble.yaml --wait --timeout 3m | grep STATUS
```

Then a "tidy-up" pull request to the chart: every component should carry an `app.kubernetes.io/component` label, so
it is added to the selector-labels helper (in a copy of the chart here):

<!-- test-run: rm -rf labs/work/ts04 && mkdir -p labs/work && cp -r charts/demo-app labs/work/ts04 -->

<!-- test: contains=component: web; output -->
```bash
sed -i 's#^app.kubernetes.io/instance: {{ .Release.Name }}#&\napp.kubernetes.io/component: web#' labs/work/ts04/templates/_helpers.tpl
sed -n '/define "demo-app.selectorLabels"/,/end/p' labs/work/ts04/templates/_helpers.tpl
```

```text
{{- define "demo-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "demo-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: web
{{- end }}
```

<!-- test: fail; timeout=300; contains=field is immutable; output -->
```bash
helm upgrade demo labs/work/ts04 --namespace trouble -f troubleshooting/values-trouble.yaml --wait --timeout 60s
```

```text
level=WARN msg="upgrade failed" name=demo error="server-side apply failed for object trouble/demo-demo-app apps/v1, Kind=Deployment: Deployment.apps \"demo-demo-app\" is invalid: spec.selector: Invalid value: {\"matchLabels\":{\"app.kubernetes.io/component\":\"web\",\"app.kubernetes.io/instance\":\"demo\",\"app.kubernetes.io/name\":\"demo-app\"}}: field is immutable"
Error: UPGRADE FAILED: server-side apply failed for object trouble/demo-demo-app apps/v1, Kind=Deployment: Deployment.apps "demo-demo-app" is invalid: spec.selector: Invalid value: {"matchLabels":{"app.kubernetes.io/component":"web","app.kubernetes.io/instance":"demo","app.kubernetes.io/name":"demo-app"}}: field is immutable
```

## Problem

The upgrade failed, so "nothing changed"? But the application is down.

## Symptoms

<!-- test: retry=15; contains=no available server; output -->
```bash
curl -s http://trouble.localhost:8080/; echo
```

```text
no available server
```

<!-- test: contains=1/1; output -->
```bash
kubectl get pods --namespace trouble
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
demo-demo-app-68d8b4d8dc-4xz6t   1/1     Running   0          5s
```

The Pod is `Running` and `1/1` Ready. The application is healthy; the traffic does not reach it.

## Investigation

Healthy Pods and failing traffic means the problem is **between** the Service and the Pods. A Service sends traffic to
its **endpoints**: the Ready Pods whose labels match its selector.

## Commands

<!-- test: contains=<none>; output -->
```bash
kubectl get endpointslices --namespace trouble -l kubernetes.io/service-name=demo-demo-app \
  -o custom-columns='NAME:.metadata.name,ENDPOINTS:.endpoints[*].addresses[0]'
```

```text
NAME                  ENDPOINTS
demo-demo-app-k6rzq   <none>
```

No endpoints. Compare the Service's selector with the Pod's labels:

<!-- test: contains=component; output -->
```bash
kubectl get service demo-demo-app --namespace trouble -o jsonpath='{.spec.selector}'; echo
kubectl get pods --namespace trouble --show-labels
```

```text
{"app.kubernetes.io/component":"web","app.kubernetes.io/instance":"demo","app.kubernetes.io/name":"demo-app"}
NAME                             READY   STATUS    RESTARTS   AGE   LABELS
demo-demo-app-68d8b4d8dc-4xz6t   1/1     Running   0          5s    app.kubernetes.io/instance=demo,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=demo-app,app.kubernetes.io/part-of=bookshop,app.kubernetes.io/version=1.0.0,environment=dev,helm.sh/chart=demo-app-1.0.0,pod-template-hash=68d8b4d8dc
```

And what did the failed upgrade do?

<!-- test: contains=failed; output -->
```bash
helm history demo --namespace trouble
```

```text
REVISION	UPDATED                 	STATUS  	CHART         	APP VERSION	DESCRIPTION                                                                                                                                                                                                                                                                                                                           
1       	Mon Oct  5 01:08:18 2026	deployed	demo-app-1.0.0	1.0.0      	Install complete                                                                                                                                                                                                                                                                                                                      
2       	Mon Oct  5 01:08:21 2026	failed  	demo-app-1.0.0	1.0.0      	Upgrade "demo" failed: server-side apply failed for object trouble/demo-demo-app apps/v1, Kind=Deployment: Deployment.apps "demo-demo-app" is invalid: spec.selector: Invalid value: {"matchLabels":{"app.kubernetes.io/component":"web","app.kubernetes.io/instance":"demo","app.kubernetes.io/name":"demo-app"}}: field is immutable
```

## Output Interpretation

- The Service selects `app.kubernetes.io/component=web`; the Pod has no such label. No match → no endpoints →
  Traefik has nowhere to send requests (`no available server`).
- The upgrade **partially applied**: Helm updated the Service (allowed: a Service's selector can change), then the
  API server rejected the Deployment: `spec.selector: ... field is immutable`. Helm stops at the first error; it does
  not undo what it already applied. Revision 2 is `failed`, and the cluster is a mix of revision 1 and revision 2.

## Root Cause

The selector-labels helper is used by **both** the Service selector and the Deployment's `spec.selector`. A
Deployment's selector can never change after creation (Kubernetes would otherwise lose track of which Pods belong to
it). So the change could never succeed for an existing release, and the half that did succeed broke routing.

## Fix

Go back to the last good revision: the rollback re-applies revision 1's Service selector.

<!-- test: timeout=300; contains=Rollback was a success -->
```bash
helm rollback demo 1 --namespace trouble --wait --timeout 3m
```

Then fix the chart change itself: add new labels to the **common** labels (`demo-app.labels`), never to the selector
labels of an existing chart. If a selector must change, it is a breaking change: a new major chart version, and the
Deployment must be recreated (uninstall/reinstall, or a new release name).

## Verification

<!-- test: retry=20; contains=APP_ENV: "dev"; output -->
```bash
kubectl get endpointslices --namespace trouble -l kubernetes.io/service-name=demo-demo-app \
  -o custom-columns='NAME:.metadata.name,ENDPOINTS:.endpoints[*].addresses[0]'
curl -s http://trouble.localhost:8080/config.js; echo
helm history demo --namespace trouble | tail -1
```

```text
NAME                  ENDPOINTS
demo-demo-app-k6rzq   10.244.1.98
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

3       	Mon Oct  5 01:08:25 2026	deployed  	demo-app-1.0.0	1.0.0      	Rollback to 1                                                                                                                                                                                                                                                                                                                         
```

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
rm -rf labs/work/ts04
```

## Lesson Learned

- Pods fine, traffic failing → `kubectl get endpointslices`; empty means selector mismatch (or no Ready Pod).
- The Service selector, the Deployment selector and the Pod labels must agree; they come from one helper so they
  always do, and that helper must stay stable.
- A failed upgrade is not "nothing happened". Objects applied before the error stay changed. `helm rollback` (or
  `--rollback-on-failure`) brings everything back to one consistent revision.
- Review selector changes with a render diff before merging (`helm template` old vs new, or `kubectl diff`).
