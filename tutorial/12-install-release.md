# Chapter 12 · Install a release

> Lesson: [lab 07](../labs/07-install-release.md). Time: 35 minutes.

## Do

The whole lab: install `demo` into `demo-dev`, inspect it from both sides, find the release Secret, install and
uninstall a throwaway release, then the challenge (a second release in the same namespace).

## Watch for

```text
NAME                         TYPE                 DATA   AGE   LABELS
sh.helm.release.v1.demo.v1   helm.sh/release.v1   1      5s    ...,name=demo,owner=helm,status=deployed,version=1
```

and in `helm get metadata`:

```text
APPLY_METHOD: server-side apply
```

## Think like an engineer

A Helm installation creates a Helm release, and the release lives **in the cluster**: one Secret per revision,
holding the chart, the values and the rendered manifest. That is why `helm get manifest` works without the chart
folder, why your teammates see the same `helm list`, and why rollback can restore any kept revision.

After an uninstall, check the namespace, not just `helm list`: namespaces created with `--create-namespace`,
StatefulSet volumes, objects with `resource-policy: keep` and hook objects are not part of the release.

## Checkpoint

- [ ] You can answer "what did this release get?" (`helm get values`) and "what did Helm apply?" (`helm get manifest`).
- [ ] You know where a release is stored and what happens if those Secrets are deleted.
- [ ] Two releases of one chart ran side by side in `demo-dev`.

Next: [13 · Upgrade a release](13-upgrade.md).
