# 12 · Values conflict

> Uses demo-app in namespace `trouble` with the **production** values. Time: 15 minutes.

## Break it

Production, from its values file (autoscaling between 3 and 6 replicas):

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install demo charts/demo-app --namespace trouble --create-namespace \
  -f charts/demo-app/values-prod.yaml --wait --timeout 3m | grep STATUS
```

A sale starts tomorrow. The request: "run 5 replicas". The precedence rules say `--set` beats every values file, so:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble \
  -f charts/demo-app/values-prod.yaml --set replicaCount=5 --wait --timeout 3m | grep STATUS
```

## Problem

The upgrade succeeded, and there are still 3 Pods.

## Symptoms

<!-- test: retry=20; contains=3/3; output -->
```bash
kubectl get deployment demo-demo-app --namespace trouble
```

```text
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
demo-demo-app   3/3     3            3           2s
```

## Investigation

Precedence worked as documented? Check that the value arrived, then follow it into the rendered objects.

## Commands

<!-- test: contains=replicaCount: 5; contains=minReplicas: 3; output -->
```bash
helm get values demo --namespace trouble | grep -E 'replicaCount|enabled|minReplicas|maxReplicas'
```

```text
  enabled: true
  maxReplicas: 6
  minReplicas: 3
  enabled: true
replicaCount: 5
```

<!-- test: contains=HorizontalPodAutoscaler; output -->
```bash
helm get manifest demo --namespace trouble | grep -E '^kind:|replicas:|minReplicas|maxReplicas'
```

```text
kind: ServiceAccount
kind: ConfigMap
kind: Service
kind: Deployment
kind: HorizontalPodAutoscaler
  minReplicas: 3
  maxReplicas: 6
kind: Ingress
```

<!-- test: contains=demo-demo-app; output -->
```bash
kubectl get hpa --namespace trouble
```

```text
NAME            REFERENCE                  TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
demo-demo-app   Deployment/demo-demo-app   cpu: <unknown>/70%   3         6         1          3s
```

And the template that decides:

<!-- test: contains=autoscaling.enabled; output -->
```bash
grep -n -B1 -A2 'replicaCount' charts/demo-app/templates/deployment.yaml
```

```text
8-  {{- if not .Values.autoscaling.enabled }}
9:  replicas: {{ .Values.replicaCount }}
10-  {{- end }}
11-  selector:
```

## Output Interpretation

- `replicaCount: 5` **is** in the release's values: `--set` won, precedence worked.
- But the rendered manifest has no `replicas:` in the Deployment at all, and an HPA with `minReplicas: 3`. The template
  only uses `replicaCount` when `autoscaling.enabled` is false.
- With autoscaling on, the HorizontalPodAutoscaler owns the replica count: between `minReplicas` and `maxReplicas`,
  driven by CPU. `replicaCount` is not a conflict Helm resolves; it is simply not used.

## Root Cause

Two values that look independent are coupled in the template: `autoscaling.enabled: true` (from the prod file) makes
`replicaCount` (from `--set`) irrelevant. Values precedence decides **which value** a key gets; the chart decides
**whether a key matters**.

## Fix

Express the intent in the setting that is actually in charge, the autoscaler's floor, and in the values file rather
than a `--set` that the next deployment would forget:

<!-- test: contains=minReplicas: 5 -->
```bash
mkdir -p labs/work
cp charts/demo-app/values-prod.yaml labs/work/values-prod-sale.yaml
sed -i 's/^  minReplicas: 3/  minReplicas: 5   # sale: at least 5, until the end of the campaign/' labs/work/values-prod-sale.yaml
grep minReplicas labs/work/values-prod-sale.yaml
```

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f labs/work/values-prod-sale.yaml --wait --timeout 3m | grep STATUS
```

## Verification

<!-- test: retry=30; contains=5/5; output -->
```bash
kubectl get hpa,deployment --namespace trouble
```

```text
NAME                                                REFERENCE                  TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/demo-demo-app   Deployment/demo-demo-app   cpu: <unknown>/70%   5         6         3          10s

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/demo-demo-app   5/5     5            5           10s
```

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
kubectl delete namespace trouble > /dev/null
rm -f labs/work/values-prod-sale.yaml
```

## Lesson Learned

- "My value has no effect": first `helm get values` (did it arrive?), then `helm get manifest` (did it render?), then
  the template (which conditions use it?).
- Precedence (`values.yaml` < `-f` files in order < `--set`) only decides a key's value. Charts can make keys depend
  on each other; good charts document it (demo-app's `values.yaml`: "Ignored when autoscaling.enabled is true").
- With an HPA, scale through `minReplicas`/`maxReplicas`, not `replicas`.
- A `--set` for a business event is forgotten on the next deploy. Put it in a values file with a comment that says
  why and until when.
