# Chapter 03 · What is Helm?

> Lesson: [Level 2 · What is Helm?](../docs/01-what-is-helm.md). Time: 20 minutes of reading.

## The idea in one picture

```text
 Chart (templates + defaults)  +  your values  ──helm──►  plain Kubernetes YAML  ──►  a release (revision 1, 2, 3 ...)
```

Helm is a **package manager** (charts with versions), a **templating engine** (values in, YAML out) and a **release
manager** (history, upgrade, rollback). Read the Level 2 page fully; it is the vocabulary of the whole course.

## The distinction to get right now

```text
version: 1.2.0       the chart: the packaging, templates, defaults
appVersion: "2.0.0"  the application it deploys by default
```

A new template option with the same application: chart version changes, app version does not. A new application
release: app version changes, and so does the chart version, because the package's contents changed. You will see
both columns in every `helm list`.

## Think like an engineer

When someone says "we're on version 3 of the payments chart", ask: chart 3 or app 3? When a chart's version did not
change but its contents did, distrust it: a published version must never change.

Helm is not a replacement for Kubernetes knowledge. Everything it creates is ordinary Deployments and Services;
when a Pod crashes, you debug it with kubectl, as always.

## Checkpoint

- [ ] You can define chart, values, template, rendered manifest, release, revision, repository.
- [ ] You can explain chart version vs app version with an example.
- [ ] You can name one thing Helm does **not** do (secret management, Kubernetes debugging).

Next: [04 · Install Helm](04-install-helm.md).
