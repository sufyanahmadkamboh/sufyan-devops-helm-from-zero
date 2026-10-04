# Chapter 18 · Helm hooks

> Lesson: [lab 13](../labs/13-hooks.md). Time: 35 minutes.

## Do

Install, upgrade and uninstall the hooks example and read the Jobs' logs in order; look at the Bookshop's report
hook; then the failing `pre-upgrade` hook and the tidy-up challenge.

## Watch for

```text
pre-install hook · release hooks · revision 1 · 21:47:15
post-install hook · release hooks · revision 1 · 21:47:18
pre-upgrade hook · release hooks · revision 2 · 21:47:21
post-upgrade hook · release hooks · revision 2 · 21:47:24
pre-delete hook · release hooks · revision 2 · 21:47:28
```

and after the failing hook, the ConfigMap still says `hello from the hooks example`: the upgrade stopped before
touching anything.

## Think like an engineer

Hooks are powerful and add moving parts: they block the operation while they run, a rollback does not undo what they
did, and their objects outlive `helm uninstall`. Before writing one, ask whether an initContainer, a normal Job, a
CronJob or a pipeline step would do. The Bookshop has exactly one hook, because a deployment report must run after
each deployment, which is precisely what `post-install,post-upgrade` means.

A failing `pre-upgrade` hook is a gate, and a good one: database migrations that fail should stop the new version
from starting.

## Checkpoint

- [ ] You can list the five common hooks and when each runs.
- [ ] You know what a failed `pre-upgrade` hook does to the release and to the objects.
- [ ] You can choose a delete policy and explain the leftovers each one leaves.

Next: [19 · Helm tests](19-tests.md).
