# Chapter 22 · Production-style chart

> Lesson: [Level 19](../docs/16-production-style-chart.md), with [charts/bookshop](../charts/bookshop) open. Time: 40 minutes.

## Do

Read the mapping table (raw YAML → chart), each design decision, then deploy staging and production next to dev and
test all three.

## Watch for

```text
== dev: 1 ConfigMap, 5 Deployment, 1 Ingress, 1 Secret, 6 Service, 1 StatefulSet,
== staging: 1 ConfigMap, 5 Deployment, 1 Ingress, 1 Secret, 6 Service, 1 StatefulSet,
== prod: 1 ConfigMap, 5 Deployment, 1 HorizontalPodAutoscaler, 1 Ingress, 5 PodDisruptionBudget, 1 Secret, 6 Service, 1 StatefulSet,
```

and the promotion gate:

```text
dev: Succeeded
staging: Succeeded
prod: Succeeded
```

## Think like an engineer

Every technique in this chart answers one problem from chapter 02: `range` removes five copies, values files hold
the differences, `tpl` builds URLs that depend on the release, `lookup` + `keep` keeps a password nobody typed, the
checksum restarts Pods on configuration changes, a condition makes the database optional, an HPA and PDBs exist only
where they make sense.

Equally important is what the chart does **not** do: no clever abstractions, no hook that isn't needed, no value that
nobody would change. A chart is read far more often than it is written.

## Checkpoint

- [ ] You can explain why services.yaml uses `$` and `dict` in its helpers.
- [ ] You can name what a real production values file would add.
- [ ] You can version a change to this chart correctly (chart vs app version).

Next: [23 · Capstone](23-capstone.md).
