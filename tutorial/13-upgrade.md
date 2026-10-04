# Chapter 13 · Upgrade a release

> Lesson: [lab 08](../labs/08-upgrade.md). Time: 35 minutes.

## Do

Review the planned change with the server-side diff, upgrade, follow the rollout, read the history and the values per
revision. Then the Break It: the "quick" upgrade without the dev file. Don't fix it until you have investigated it.

## Watch for

The review:

```text
-  replicas: 1
+  replicas: 2
-        checksum/config: 5495...
+        checksum/config: dfb1...
-  ADMIN_URL: ""
+  ADMIN_URL: http://admin.example.com
```

Three changes, and the checksum tells you the Pods will be replaced. Then the Break It result:

```text
404 page not found
USER-SUPPLIED VALUES:
replicaCount: 3
```

## Think like an engineer

`helm upgrade` renders with the values **you give in this command**. It does not remember the previous ones (unless
`--reuse-values`, which has its own traps). The upgrade "succeeded" and deleted the Ingress, because the chart's
default is `ingress.enabled: false`. That is why the exact deployment command belongs in a script or pipeline.

Helm manages the release (revision 3, 4, 5...); Kubernetes manages the rollout (the Deployment's own revisions,
`kubectl rollout history`). Two different numbers, two different jobs.

## Checkpoint

- [ ] You can preview an upgrade's effect before applying it.
- [ ] You can explain the forgotten-values failure from `helm history` and `helm get values` alone.
- [ ] You changed the Service port without breaking the Ingress, and know why it worked.

Next: [14 · Roll back a release](14-rollback.md).
