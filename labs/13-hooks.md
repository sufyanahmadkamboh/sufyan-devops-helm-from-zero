# Lab 13 · Hooks

> Level 15. Time: 35 minutes.

## Objective

See exactly when Helm runs `pre-install`, `post-install`, `pre-upgrade`, `post-upgrade` and `pre-delete` hooks, what
happens when one fails, and why hooks should be used sparingly.

## Prerequisites

- [Lab 12](12-dependencies.md): the `shop` release in `bookshop-dev`.

## Task

1. Install, upgrade and uninstall [examples/hooks-example](../examples/hooks-example) and read the order of its hooks.
2. Find the Bookshop's real hook and its output.
3. Make a hook fail and see what it does to an upgrade.

## Commands

### 1 · What a hook is

A hook is an ordinary Kubernetes object (almost always a Job) with an annotation:

<!-- test: contains=helm.sh/hook; output -->
```bash
helm template hooks examples/hooks-example --show-only templates/hooks.yaml | sed -n '1,/^spec:/p' | head -16
```

```text
---
# Source: hooks-example/templates/hooks.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: hooks-pre-install
  labels:
    app.kubernetes.io/instance: hooks
    hook: pre-install
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    # Default before-hook-creation: delete the previous Job of this hook only when it runs again. The finished Job
    # stays, so you can read its log. (hook-succeeded would delete it right after it succeeds.)
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
```

| Annotation | Meaning |
|---|---|
| `helm.sh/hook: pre-install` | **when**: before any resource of the release is created |
| `helm.sh/hook-weight: "-5"` | **order** among hooks of the same event: lower first |
| `helm.sh/hook-delete-policy` | **cleanup**: `before-hook-creation` (default), `hook-succeeded`, `hook-failed` |

Helm creates the hook object at its moment, **waits until it completes**, and only then continues. A failed hook fails
the operation. Hook objects are **not** part of the release's normal resources: no upgrade diffs, no rollback, and
`helm uninstall` does not delete them.

### 2 · Watch the order

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install hooks examples/hooks-example --namespace lab-13 --create-namespace --wait | grep STATUS
```

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade hooks examples/hooks-example --namespace lab-13 --wait | grep STATUS
```

Every hook Job printed one line with its event, the release revision and the time. Read them in creation order:

<!-- test: contains=post-upgrade hook; output -->
```bash
for job in $(kubectl get jobs --namespace lab-13 --sort-by=.metadata.creationTimestamp -o name); do
  kubectl logs --namespace lab-13 "$job"
done
```

```text
pre-install hook · release hooks · revision 1 · 23:05:17
post-install hook · release hooks · revision 1 · 23:05:20
pre-upgrade hook · release hooks · revision 2 · 23:05:24
post-upgrade hook · release hooks · revision 2 · 23:05:27
```

```text
helm install   →  pre-install Job  →  ConfigMap created  →  post-install Job      (revision 1)
helm upgrade   →  pre-upgrade Job  →  ConfigMap updated  →  post-upgrade Job      (revision 2)
```

Now uninstall:

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls the release hooks.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall hooks --namespace lab-13 --wait
```

<!-- test: contains=pre-delete; absent=hooks-settings; output -->
```bash
kubectl logs --namespace lab-13 job/hooks-pre-delete
kubectl get jobs,configmaps --namespace lab-13
```

```text
pre-delete hook · release hooks · revision 2 · 23:05:31
NAME                           STATUS     COMPLETIONS   DURATION   AGE
job.batch/hooks-post-install   Complete   1/1           3s         14s
job.batch/hooks-post-upgrade   Complete   1/1           3s         7s
job.batch/hooks-pre-delete     Complete   1/1           3s         3s
job.batch/hooks-pre-install    Complete   1/1           6s         20s
job.batch/hooks-pre-upgrade    Complete   1/1           3s         11s

NAME                         DATA   AGE
configmap/kube-root-ca.crt   1      20s
```

The `pre-delete` Job ran before the release's objects were deleted; the ConfigMap is gone. But all five hook Jobs are
**still there**: they never belonged to the release. With `before-hook-creation` they are only replaced the next time
the same hook runs. Leftovers like these are why hooks need a deliberate delete policy.

### 3 · A real hook: the Bookshop report

The bookshop chart runs one hook, [report-hook.yaml](../charts/bookshop/templates/report-hook.yaml): after every
install and upgrade (`post-install,post-upgrade`), the `report-worker` Job collects statistics from two APIs and
saves a report in the database. A good use of a hook: a task that must run at a precise moment of each deployment,
after the new version is up.

<!-- test: contains=post-install,post-upgrade; output -->
```bash
helm get hooks shop --namespace bookshop-dev | grep -E '^kind:|helm.sh/hook'
```

```text
kind: Pod
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation
kind: Job
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": before-hook-creation
```

<!-- test: contains=report #; output -->
```bash
kubectl logs --namespace bookshop-dev job/shop-report
```

```text
2026-10-04T23:04:55.741Z report-worker version 1.0.0 starting: stats from http://shop-python-api:8000/api/stats, status from http://shop-go-status:8080/api/status
2026-10-04T23:04:56.190Z report-worker report #1 saved: users=3 books=5 reviews=0 services up=5/5
```

An upgrade runs it again; `before-hook-creation` replaced the previous Job:

<!-- test: timeout=600; contains=STATUS: deployed -->
```bash
helm upgrade shop charts/bookshop --namespace bookshop-dev -f charts/bookshop/values-dev.yaml --wait --timeout 5m | grep STATUS
```

<!-- test: contains=report #2; output -->
```bash
kubectl logs --namespace bookshop-dev job/shop-report
```

```text
2026-10-04T23:05:36.359Z report-worker version 1.0.0 starting: stats from http://shop-python-api:8000/api/stats, status from http://shop-go-status:8080/api/status
2026-10-04T23:05:36.778Z report-worker report #2 saved: users=3 books=5 reviews=0 services up=5/5
```

Report #2: one report per deployment, written after the release was ready.

## Expected Output

- Hook logs in order: `pre-install` (rev 1), `post-install` (rev 1), `pre-upgrade` (rev 2), `post-upgrade` (rev 2),
  then `pre-delete` on uninstall.
- After uninstall: the five hook Jobs remain, the ConfigMap is gone.
- The Bookshop report count increases with each upgrade.

## Explanation

Hooks are powerful and add moving parts. Before writing one, ask whether something simpler does the job:

| Need | Simpler than a hook |
|---|---|
| Wait for the database before the app starts | an `initContainer`, or a readiness probe + retries in the app |
| Configuration files | a ConfigMap (normal resource, diffed, rolled back) |
| Run something on a schedule | a CronJob (normal resource) |
| Database migration **before** the new version starts | a `pre-upgrade` hook is reasonable, if the migration is backwards compatible (a rollback does not undo it) |
| A smoke check or notification after a deployment | a `post-install/post-upgrade` hook, or a step in the CI/CD pipeline |

Cautions:

- A rollback does not undo what a hook did (a migration, a message sent).
- A slow hook makes every install and upgrade slow; a stuck one blocks it until `--timeout`.
- `helm template` renders hooks like any object (`--no-hooks` leaves them out); GitOps tools translate Helm hooks into
  their own mechanisms (Argo CD maps them to sync hooks), not always with identical behaviour.
- Hook objects are invisible to `helm get manifest` (use `helm get hooks`) and survive `helm uninstall`.

## Break It

A pre-upgrade hook fails (say, a migration that cannot run). `failAt` makes the example's hook exit with an error:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install hooks examples/hooks-example --namespace lab-13 --wait | grep STATUS
```

<!-- test: fail; timeout=300; contains=pre-upgrade hooks failed; output -->
```bash
helm upgrade hooks examples/hooks-example --namespace lab-13 \
  --set failAt=pre-upgrade --set message="new message" --wait --timeout 2m
```

```text
level=WARN msg="upgrade failed" name=hooks error="pre-upgrade hooks failed: resource Job/lab-13/hooks-pre-upgrade not ready. status: Failed, message: Job Failed. failed: 1/1"
Error: UPGRADE FAILED: pre-upgrade hooks failed: resource Job/lab-13/hooks-pre-upgrade not ready. status: Failed, message: Job Failed. failed: 1/1
```

## Troubleshoot It

The error names the hook (`Job/lab-13/hooks-pre-upgrade`) and its state (`Failed`). Its log says why:

<!-- test: contains=simulated failure; output -->
```bash
kubectl logs --namespace lab-13 job/hooks-pre-upgrade
```

```text
pre-upgrade hook · release hooks · revision 2 · 23:05:46
pre-upgrade: simulated failure (failAt=pre-upgrade)
```

What did the failure do to the release?

<!-- test: contains=failed; contains=hello from the hooks example; output -->
```bash
helm history hooks --namespace lab-13
kubectl get configmap hooks-settings --namespace lab-13 -o jsonpath='{.data.MESSAGE}'; echo
```

```text
REVISION	UPDATED                 	STATUS  	CHART              	APP VERSION	DESCRIPTION                                                                                                                                        
1       	Mon Oct  5 01:05:39 2026	deployed	hooks-example-0.1.0	1.0.0      	Install complete                                                                                                                                   
2       	Mon Oct  5 01:05:45 2026	failed  	hooks-example-0.1.0	1.0.0      	Upgrade "hooks" failed: pre-upgrade hooks failed: resource Job/lab-13/hooks-pre-upgrade not ready. status: Failed, message: Job Failed. failed: 1/1
hello from the hooks example
```

Revision 2 is `failed`, and the ConfigMap still has the **old** message: a failed `pre-upgrade` hook stops the upgrade
before any resource is touched. That is the purpose of a pre-upgrade hook: a gate. Fix the cause (here, drop
`failAt`) and upgrade again:

<!-- test: timeout=300; contains=new message -->
```bash
helm upgrade hooks examples/hooks-example --namespace lab-13 --set message="new message" --wait > /dev/null
kubectl get configmap hooks-settings --namespace lab-13 -o jsonpath='{.data.MESSAGE}'; echo
```

## Challenge

The finished `post-install` Job lingers forever. Make that one hook delete itself as soon as it succeeds, without
changing the template, and prove it is gone after an install.

## Solution

<details>
<summary>Open the solution</summary>

The template reads an optional `deletePolicy` per hook entry. Lists in values are replaced as a whole, so the file
repeats every entry:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
cat > labs/work/hooks-tidy.yaml <<'EOF'
hooks:
  - { event: pre-install, weight: -5 }
  - { event: post-install, weight: 0, deletePolicy: hook-succeeded }
  - { event: pre-upgrade, weight: 0 }
  - { event: post-upgrade, weight: 0 }
  - { event: pre-delete, weight: 0 }
EOF
helm install tidy examples/hooks-example --namespace lab-13 -f labs/work/hooks-tidy.yaml --wait | grep STATUS
```

</details>

## Verification

<!-- test: contains=tidy-pre-install; absent=tidy-post-install; output -->
```bash
kubectl get jobs --namespace lab-13 -o name | grep tidy
```

```text
job.batch/tidy-pre-install
```

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls hooks and tidy, deletes the namespace lab-13 (and the leftover hook Jobs with it).
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall hooks tidy --namespace lab-13 --wait
kubectl delete namespace lab-13 --wait=false > /dev/null
rm -f labs/work/hooks-tidy.yaml
```

Next: [lab 14 · Tests and NOTES](14-tests.md).
