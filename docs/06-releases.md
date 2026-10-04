# Releases: install, status, history, uninstall

> Hands-on: [lab 07](../labs/07-install-release.md).

## 1 · What is it?

A **release** is one installed instance of a chart: a name, a namespace, and a numbered history of **revisions**.
Each revision stores the chart, the values and the rendered manifest, with a status (`deployed`, `superseded`,
`failed`, `pending-install/upgrade/rollback`, `uninstalling`).

## 2 · Why do we need it?

To know what is deployed, with which configuration, since when, and to act on the application as a whole: upgrade it,
roll it back, remove it.

## 3 · How does it work?

`helm install` renders the chart, applies the objects (Helm 4: server-side apply), and stores revision 1 as a Secret
`sh.helm.release.v1.<name>.v1` in the release's namespace. Every later operation adds a revision. Helm keeps the last
10 revisions by default (`--history-max`).

## 4 · What problem does it solve?

`kubectl apply` keeps no record of what you applied as a whole. A release does.

## 5 · How do I use it?

`helm upgrade --install` with `--wait` from a pipeline; `helm list/status/history/get` to inspect; `helm uninstall`
to remove.

## 6 · What command should I run?

| Command | When |
|---|---|
| `helm install NAME CHART -n NS --create-namespace -f values.yaml --wait` | first deployment |
| `helm list [-A]` | what is installed, which chart/app versions |
| `helm status NAME` | current status and NOTES |
| `helm history NAME` | every revision and what happened |
| `helm get values\|manifest\|notes\|hooks\|metadata\|all NAME [--revision N]` | what exactly a revision contains |
| `helm uninstall NAME --wait` | remove the release's objects and history |

## 7 · What output should I expect?

`STATUS: deployed`, `REVISION: 1`, then the NOTES. `helm list` columns: `NAME NAMESPACE REVISION UPDATED STATUS CHART APP VERSION`.

## 8 · What can go wrong?

`cannot reuse a name that is still in use` (use `upgrade --install`); `deployed` without `--wait` while Pods fail
([03](../troubleshooting/03-incorrect-image.md)); release Secrets deleted by hand (Helm forgets the release, objects
stay); `forbidden` on Secrets (RBAC).

## 9 · How do I troubleshoot it?

`helm status` and `helm history` for Helm's view; `kubectl get ... -l app.kubernetes.io/instance=NAME` for the
cluster's; `helm get manifest | kubectl diff --server-side --field-manager=helm -f -` for drift between them.

## 10 · Where is it used in real DevOps work?

Tracking application deployments: "which version runs in staging, deployed when, with which values?" is answered
by `helm list` and `helm get values`.

## What `helm uninstall` removes and leaves

| Removed | Left behind |
|---|---|
| every object in the release's manifest | the namespace |
| all revision Secrets | PVCs from StatefulSet `volumeClaimTemplates` |
| | objects with `helm.sh/resource-policy: keep` |
| | hook objects (unless their delete policy removed them) |
| | CRDs from a chart's `crds/` folder |

Verify after uninstalling: `helm list -n NS` and `kubectl get all,pvc,secret,configmap -n NS`.
