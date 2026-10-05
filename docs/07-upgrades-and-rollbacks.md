# Upgrades and rollbacks

> Hands-on: [lab 08](../labs/08-upgrade.md), [lab 09](../labs/09-rollback.md), troubleshooting
> [06](../troubleshooting/06-failed-upgrade.md) and [07](../troubleshooting/07-bad-revision-rollback.md).

## 1 · What is it?

`helm upgrade` applies a new chart version and/or new values to a release, as a new revision. `helm rollback` applies
an earlier revision's manifest and values again, as a new revision.

## 2 · Why do we need it?

Deploying new application versions and configuration changes, and recovering quickly when one goes wrong.

## 3 · How does it work?

```text
helm upgrade ─► render ─► apply changed/new objects, delete removed ones ─► Kubernetes rolling update
                          (new ReplicaSet, new Pods Ready, old Pods removed) ─► --wait until ready ─► revision N
helm rollback REL M ─► apply revision M's manifest ─► revision N+1 "Rollback to M"
```

Helm manages the release; Kubernetes manages the workloads (`kubectl rollout status/history` shows the Deployment's
side).

## 4 · What problem does it solve?

Safe change: every change is recorded, reviewable, and reversible as a whole.

## 5 · How do I use it?

Review first (`helm template ... | kubectl diff --server-side --field-manager=helm -f -`), always pass the complete
values files, use `--wait` (and `--rollback-on-failure` in pipelines), verify with `helm test`.

## 6 · What command should I run?

```bash
helm upgrade demo charts/demo-app -n demo-dev -f charts/demo-app/values-dev.yaml --wait --timeout 3m
kubectl rollout status deployment/demo-demo-app -n demo-dev
helm history demo -n demo-dev
helm rollback demo 2 -n demo-dev --wait
helm upgrade ... --rollback-on-failure --timeout 60s     # automatic rollback (Helm 3: --atomic)
```

## 7 · What output should I expect?

`Release "demo" has been upgraded. Happy Helming!`; `Rollback was a success! Happy Helming!`; history lines
`Upgrade complete`, `Rollback to N`, or `failed` with the reason.

## 8 · What can go wrong?

| Problem | Where |
|---|---|
| Forgotten values files → defaults | [lab 08](../labs/08-upgrade.md#break-it) |
| Upgrade never ready (image, probes, a missing service account) | [lab 09](../labs/09-rollback.md), [06](../troubleshooting/06-failed-upgrade.md) |
| Successful but wrong upgrade | [07](../troubleshooting/07-bad-revision-rollback.md) |
| Partially applied failed upgrade (immutable field) | [04](../troubleshooting/04-wrong-service-selector.md) |
| `another operation ... is in progress` | interrupted operation, [lab 09](../labs/09-rollback.md#break-it) |
| Server-side apply conflict | a field changed by another tool, [11](../troubleshooting/11-failed-helm-test.md) |

## 9 · How do I troubleshoot it?

`helm history` → `helm get values/manifest --revision N` diffs → `kubectl get pods`, `describe`, events of the new
Pods.

## 10 · Where is it used in real DevOps work?

Upgrades: deploying a new application version. Rollbacks: recovering from failed deployments, the first move in an
incident caused by a change. Remember that a rollback restores objects, not data.
