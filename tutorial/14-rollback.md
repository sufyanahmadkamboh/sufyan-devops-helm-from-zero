# Chapter 14 · Roll back a release

> Lesson: [lab 09](../labs/09-rollback.md). Time: 40 minutes. The most important practical lab of the course.

## Do

All of it, in order: two good revisions, a bad upgrade, the investigation, the rollback, the automatic rollback, the
interrupted upgrade.

## Watch for

The bad upgrade:

```text
Error: UPGRADE FAILED: resource Deployment/demo-rollback/demo-demo-app not ready. status: InProgress, ...
context deadline exceeded
```

and, while it is failing:

```text
demo-demo-app-56457858d8-bkjwk   1/1     Running        0          67s
demo-demo-app-6dc6b54f46-n2fxb   0/1     ErrImagePull   0          61s
```

The old Pod is still serving. After `helm rollback demo 2`:

```text
4       ...   deployed    ...   Rollback to 2
```

## Think like an engineer

This is where Helm history becomes useful. A rollback never rewrites history: it adds a revision that copies an older
one. The record stays honest, including the failure.

Note what saved users during the failure: Kubernetes' rolling update, not Helm. Helm noticed the failure because of
`--wait`; without it, the bad revision would have been reported as `deployed`.

The killed upgrade is the one you will meet in real life (a CI runner that dies mid-deploy): `another operation
(install/upgrade/rollback) is in progress`. The lock is real, the operation is dead, and the fix is a rollback to the
last good revision, after making sure nobody else is deploying.

And remember the limit: a rollback restores objects, not data.

## Checkpoint

- [ ] You can find the last good revision and roll back to it.
- [ ] You can explain what `--rollback-on-failure` does and when it does not help (a "successful" bad release).
- [ ] You recovered a release stuck in `pending-upgrade`.

Next: [15 · Environment-specific values](15-environments.md).
