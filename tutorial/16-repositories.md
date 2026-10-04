# Chapter 16 · Helm repositories

> Lesson: [lab 11](../labs/11-repositories.md). Time: 40 minutes.

## Do

Read a repository's `index.yaml`, add podinfo, search, review the chart, install a pinned version with a values file,
pull it from OCI, publish demo-app to a local registry, then the upgrade challenge (6.14.1 → 6.15.0).

## Watch for

The review of what podinfo would create:

```text
      1           image: "ghcr.io/stefanprodan/podinfo:6.14.1"
      1       image: curlimages/curl:7.69.0
      1       image: giantswarm/tiny-tools
      1       image: stefanprodan/grpc_health_probe:v0.3.0
```

The application image from the maintainer's registry, and three more images in its test Pods, one without a tag.

## Think like an engineer

Helm is also how you consume charts other teams and projects write: ingress controllers, cert-manager, monitoring.
Treat every one as code you are about to run with your credentials: who publishes it, which version, what it
creates, which images it pulls. Pin `--version` always; a digest pins harder.

Upgrading a third-party chart is two upgrades at once (the chart and the application): diff the renders of both
versions with your values before you upgrade, as in the challenge.

## Checkpoint

- [ ] You can explain the difference between an HTTP chart repository and an OCI registry.
- [ ] You reviewed a third-party chart's objects and images before installing it.
- [ ] You pushed a chart to an OCI registry and installed it from there.

Next: [17 · Chart dependencies](17-dependencies.md).
