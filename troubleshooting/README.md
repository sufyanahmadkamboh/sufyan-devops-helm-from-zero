# Troubleshooting labs

> Level 18. Twelve broken Helm deployments, each broken on purpose and investigated step by step. Time: 10–15 minutes
> each. Run them in order or pick one; every scenario sets up its own starting point and cleans up after itself.

Don't just read the fix. Each lab follows the order you would use in production:

```text
Problem → Symptoms → Investigation → Commands → Output Interpretation → Root Cause → Fix → Verification → Lesson Learned
```

| # | Scenario | Where it breaks | Key commands |
|---|---|---|---|
| [01](01-template-syntax-error.md) | Template syntax error | before anything reaches the cluster | `helm lint`, `helm template --debug` |
| [02](02-wrong-value.md) | Wrong value | Pods start, never become Ready | `helm get values`, `helm get manifest`, `kubectl describe` |
| [03](03-incorrect-image.md) | Incorrect image | Pods never start | `kubectl get pods`, `describe`, `logs` |
| [04](04-wrong-service-selector.md) | Wrong Service selector | Pods fine, no traffic | `kubectl get endpointslices`, `--show-labels` |
| [05](05-wrong-environment-values.md) | Wrong environment values | runs, with the wrong configuration | `helm get values`, `helm history` |
| [06](06-failed-upgrade.md) | Failed upgrade | upgrade fails, old version still serving | `helm status`, `kubectl get events` |
| [07](07-bad-revision-rollback.md) | Bad release revision | upgrade "succeeds", application broken | `helm history`, `helm get values --revision`, `helm rollback` |
| [08](08-missing-configmap.md) | Missing ConfigMap | Pods fail after a restart | `kubectl describe pod`, `helm get manifest` |
| [09](09-secret-problem.md) | Secret problem | `CreateContainerConfigError` | `kubectl get secret`, `helm get values` |
| [10](10-dependency-problem.md) | Dependency problem | chart cannot be built | `helm dependency list/update` |
| [11](11-failed-helm-test.md) | Failed Helm test | `helm test` fails, then `helm upgrade` conflicts | `helm test --logs`, server-side diff, `--force-conflicts` |
| [12](12-values-conflict.md) | Values conflict | a value "has no effect" | values precedence, `helm get manifest` |

Scenarios 01–07, 11 and 12 use [demo-app](../charts/demo-app) in the namespace `trouble`, on
`http://trouble.localhost:8080`, with [values-trouble.yaml](values-trouble.yaml). Scenarios 08 and 09 use the
`shop` release in `bookshop-dev` ([lab 12](../labs/12-dependencies.md)). Scenario 10 needs no cluster.

## The investigation toolkit

| Question | Helm | Kubernetes |
|---|---|---|
| What did I ask for? | `helm get values REL [--revision N]` | |
| What did Helm apply? | `helm get manifest REL [--revision N]` | |
| What happened when? | `helm history REL`, `helm status REL` | `kubectl get events --sort-by=.lastTimestamp` |
| What is running? | | `kubectl get pods,deploy,svc,ingress -l app.kubernetes.io/instance=REL` |
| Why is a Pod unhappy? | | `kubectl describe pod`, `kubectl logs [--previous]` |
| Does the live state match the release? | `helm get manifest REL \| kubectl diff --server-side --field-manager=helm -f -` | |
| Would my change render? | `helm lint`, `helm template --debug` | `--dry-run=server` |

A general order that works: **render** (is the chart valid?) → **compare** (is what Helm applied what I meant?) →
**observe** (what does Kubernetes say about the objects?) → **fix in values or chart, never only in the cluster** →
**verify** (`helm test`, the application itself).
