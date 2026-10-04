# Chart dependencies

> Hands-on: [lab 12](../labs/12-dependencies.md), [troubleshooting 10](../troubleshooting/10-dependency-problem.md).

## 1 · What is it?

A parent chart that includes other charts (subcharts), declared in its `Chart.yaml`:

```yaml
dependencies:
  - name: postgres
    version: 0.1.1
    repository: "file://../postgres"   # or https://..., oci://...
    condition: postgres.enabled        # optional switch
    alias: db                          # optional local name
```

```text
Parent chart (bookshop)
     ├── Application (templates/: 5 services, config, secret, ingress, hook, test)
     └── Dependency (charts/postgres-0.1.1.tgz)
           └── Database (StatefulSet + volume + Service)
```

## 2 · Why do we need it?

To install an application together with the components it needs, as one release.

## 3 · How does it work?

`helm dependency update` resolves versions, downloads packages into `charts/`, writes `Chart.lock`; `helm dependency
build` restores exactly what the lock says. At install, subcharts render with their own templates and the values the
parent puts under their name; all objects belong to the parent's release.

## 4 · What problem does it solve?

Packaging applications with required components, without copying the components' templates.

## 5 · How do I use it?

Pin versions; commit `Chart.lock`, not the `.tgz`; run `helm dependency build` in CI; switch optional components with
`condition`; configure them through the parent's values.

## 6 · What command should I run?

```bash
helm dependency list charts/bookshop
helm dependency update charts/bookshop     # after changing dependencies in Chart.yaml
helm dependency build charts/bookshop      # fresh clone / CI
```

## 7 · What output should I expect?

`helm dependency list`: `STATUS ok` for each dependency (`missing` before build/update).

## 8 · What can go wrong?

`found in Chart.yaml, but missing in charts/ directory`; `Chart.lock is out of sync`; `can't get a valid version`;
subchart values under the wrong key (they must be under the dependency's name or alias).

## 9 · How do I troubleshoot it?

`helm dependency list`; compare `Chart.yaml`, `Chart.lock` and what the source offers; `helm template` and look for
`helm.sh/chart: <subchart>-<version>` labels.

## 10 · Where is it used in real DevOps work?

Umbrella charts for a whole product, applications bundling a cache or database for dev/CI, shared library charts.

## When to use a dependency, and when not

| Dependency | Separate release |
|---|---|
| Exists only for this app, same lifecycle | Shared by many apps (ingress, monitoring) |
| Dev, CI, demos: one command for everything | Production databases: managed service or operator, own backups and upgrades |
| Always installed and removed together | Owned by another team, upgraded on its own schedule |
