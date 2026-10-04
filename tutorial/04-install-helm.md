# Chapter 04 · Install Helm

> Lesson: [lab 01](../labs/01-install-helm.md). Time: 15 minutes.

## Do

Install Helm 4 with an official method (the install script `get-helm-4`, Homebrew, winget/Chocolatey/Scoop, or the
release archive), then run the whole lab.

## Watch for

```text
version.BuildInfo{Version:"v4.3.0", ..., KubeClientVersion:"v1.37"}
```

and `helm list --all-namespaces` showing the `traefik` release from chapter 01. Then `helm env`: notice that no
variable points at the releases. They live in the cluster.

## Think like an engineer

Helm has no server and no permissions of its own: it uses your kubeconfig, like kubectl. Two consequences you will
meet again: what you cannot do with kubectl, you cannot do with Helm; and anyone with access to the namespace sees the
same releases you do.

The lab's troubleshooting table mentions two copies of Helm on the `PATH`. That is not theory: while this course was
being built, an older Helm earlier on the `PATH` made every hook wait for its full timeout (a fixed upstream bug).
`helm version` first, always.

## Checkpoint

- [ ] `helm version --short` prints v4.3 or newer.
- [ ] You know which file holds your repository list (`HELM_REPOSITORY_CONFIG`).
- [ ] You read the error of `helm list --kube-context does-not-exist` and know how to list valid contexts.

Next: [05 · Create your first chart](05-first-chart.md).
