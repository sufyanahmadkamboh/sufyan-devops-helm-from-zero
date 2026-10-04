# Reviewing changes before an upgrade (Helm diff)

> Hands-on: [lab 08](../labs/08-upgrade.md#1--review-before-you-upgrade), [lab 16 step 13](../labs/16-capstone.md#13--upgrade-the-application).

## 1 · What is it?

Seeing exactly what an upgrade will change in the cluster, before running it.

## 2 · Why do we need it?

A one-line values change can delete an Ingress, restart every Pod or change a selector. A diff of the **result** shows
that; a diff of the values file does not.

## 3 · How does it work?

Render the new state, and let the API server compute what applying it would do, without changing anything:

```bash
helm template demo charts/demo-app -n demo-dev --skip-tests -f charts/demo-app/values-dev.yaml --set replicaCount=2 \
  | kubectl diff --server-side --field-manager=helm -n demo-dev -f - \
  | grep -E '^[-+] ' | grep -vE 'generation:|meta\.helm\.sh/|^-\s+annotations:$' || true
```

`--server-side --field-manager=helm` makes the preview behave like Helm 4's own apply; the `grep`s drop noise (Helm's
ownership annotations, `generation`). The same pipeline with `helm get manifest REL` as input finds **drift**
between the release and the cluster ([lab 14](../labs/14-tests.md#troubleshoot-it)).

## 4 · What problem does it solve?

Surprises during deployments; "LGTM" reviews of changes nobody actually saw.

## 5 · How do I use it?

In a pull request job (render and diff against the target environment) and before every manual upgrade.

## 6 · What command should I run?

The pipeline above, or the optional [helm-diff plugin](https://github.com/databus23/helm-diff):

```bash
helm plugin install https://github.com/databus23/helm-diff --version v3.15.15 --verify=false
helm diff upgrade demo charts/demo-app -n demo-dev -f charts/demo-app/values-dev.yaml
```

The plugin is popular and maintained; it is still a third-party binary that runs with your credentials. Pin its
version, and note that Helm 4 requires `--verify=false` for plugins installed from Git (they carry no signature).

## 7 · What output should I expect?

`-` lines (live) and `+` lines (after the upgrade), per object.

## 8 · What can go wrong?

Secrets generated with `randAlphaNum` + `lookup` always show as changed in `helm template` (no `lookup` without a
cluster): filter them; fields owned by other tools show conflicts (add `--force-conflicts` to the preview only);
a client-side `kubectl diff` reports errors Helm would not hit (a changed Service port).

## 9 · How do I troubleshoot it?

Diff one object at a time (`--show-only`); compare `helm get manifest --revision N` between two revisions for
after-the-fact reviews.

## 10 · Where is it used in real DevOps work?

Change review in CI/CD, GitOps tools (Argo CD and Flux show this diff in their UIs), change-management records.
