# Chapter 17 · Chart dependencies

> Lesson: [lab 12](../labs/12-dependencies.md). Time: 45 minutes (the Bookshop's first install pulls six images).

## Do

The whole lab: the storefront example with podinfo as `catalog`, its condition, then the Bookshop chart with its own
PostgreSQL chart, the fresh-clone Break It, and the challenge.

## Watch for

```text
NAME    VERSION  REPOSITORY                               STATUS
podinfo 6.15.0   https://stefanprodan.github.io/podinfo   missing      (before)
podinfo 6.15.0   https://stefanprodan.github.io/podinfo   ok           (after helm dependency update)
```

And the whole platform from one command:

```text
shop-frontend-...     1/1   Running
shop-java-api-...     1/1   Running
shop-postgres-0       1/1   Running
shop-report-...       0/1   Completed
```

## Think like an engineer

`Chart.yaml` says what you accept, `Chart.lock` what you tested, `charts/` what will be packaged. `update` rewrites
the lock; `build` obeys it. CI always runs `build`.

Values flow down only: the parent configures the child under its name or alias; the child cannot see the parent's
values (except `global`). That is why bookshop has `database.*` for its own templates and `postgres.auth.*` for the
subchart, with a comment saying "keep them equal".

When is a dependency right? When the component exists only for this application and shares its lifecycle. A shared
ingress controller or a production database is a separate release, or a managed service.

## Checkpoint

- [ ] You can explain `dependency update` vs `dependency build`.
- [ ] You switched a dependency off with its condition and saw the parent's template react.
- [ ] The Bookshop runs in `bookshop-dev` (keep it: chapters 18–21 use it).

Next: [18 · Helm hooks](18-hooks.md).
