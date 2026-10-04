# Hooks, tests and NOTES

> Hands-on: [lab 13](../labs/13-hooks.md), [lab 14](../labs/14-tests.md), [troubleshooting 11](../troubleshooting/11-failed-helm-test.md).

## 1 · What is it?

- A **hook** is an object (usually a Job) annotated `helm.sh/hook: <event>` that Helm runs at a lifecycle moment:
  `pre-install`, `post-install`, `pre-upgrade`, `post-upgrade`, `pre-delete`, `post-delete`, `pre-rollback`,
  `post-rollback`, `test`.
- A **test** is a hook of type `test`: a Pod that `helm test` runs on demand; exit 0 = pass.
- **NOTES.txt** is a template printed after install/upgrade and by `helm status`.

## 2 · Why do we need it?

Hooks: work that must happen at a precise moment of a release (a migration before the new version, a report after
it). Tests: a one-command check that a release works. NOTES: tell the person who installed what to do next.

## 3 · How does it work?

Helm creates hook objects at their event, ordered by `helm.sh/hook-weight`, **waits** for them, and fails the
operation if one fails. Delete policies (`before-hook-creation`, `hook-succeeded`, `hook-failed`) decide when hook
objects are removed. Hook objects are not part of the release's manifest.

## 4 · What problem does it solve?

Ordering and verification that plain manifests cannot express.

## 5 · How do I use it?

Prefer normal resources; use hooks only for "at this moment" work; always set a delete policy; keep hook Jobs fast
and idempotent. Give every chart a test; run it after each deployment and on a schedule.

## 6 · What command should I run?

```bash
helm get hooks shop -n bookshop-dev
helm test shop -n bookshop-dev --logs [--filter name=shop-test-books]
helm get notes shop -n bookshop-dev
helm install ... --no-hooks            # skip hooks (rarely a good idea)
```

## 7 · What output should I expect?

`helm test`: `TEST SUITE`, `Phase: Succeeded`, and with `--logs` the test Pod's output.

## 8 · What can go wrong?

A failing `pre-upgrade` hook stops the upgrade before any change ([lab 13](../labs/13-hooks.md#break-it)); slow
hooks slow every deployment; leftover hook Jobs; tests that pass while the app is broken (a test that ignores
errors: [lab 14](../labs/14-tests.md) shows `set -e` and command substitution); drift that only a test notices.

## 9 · How do I troubleshoot it?

The error names the hook object; `kubectl logs job/<hook>`; `helm history` shows the failed revision; `helm test
--logs` shows which check failed.

## 10 · Where is it used in real DevOps work?

Database migrations (`pre-upgrade`), post-deployment smoke tests and notifications, pipeline gates (`helm test`
after `helm upgrade`), validating chart deployments in CI.
