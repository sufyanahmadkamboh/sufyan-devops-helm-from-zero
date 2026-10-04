# hooks-example

A Job for each of the five common hooks. Install, upgrade and uninstall it, and read the Jobs' logs to see the
order Helm runs them in.

```text
helm install  → pre-install Job → ConfigMap created → post-install Job
helm upgrade  → pre-upgrade Job → ConfigMap updated → post-upgrade Job
helm uninstall → pre-delete Job → ConfigMap deleted   (hook Jobs are not deleted: they are not release resources)
```

Used in [lab 13 · Hooks](../../labs/13-hooks.md). Hooks are powerful and add moving parts: use them only for work that
must happen at a precise moment of a release (a database migration before the new version starts, a smoke check
after it). Most things belong in normal resources.
