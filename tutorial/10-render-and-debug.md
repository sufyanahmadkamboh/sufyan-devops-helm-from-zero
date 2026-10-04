# Chapter 10 · Render and debug templates

> Lesson: [lab 06](../labs/06-rendering.md), sections 1–2. Time: 25 minutes.

## Do

Render demo-app for dev (whole, one file, to a folder), then the bookshop Secret twice, then an install with
`--dry-run=server`.

## Watch for

```text
two renders, two different passwords
```

The bookshop chart keeps its database password stable with `lookup`, which reads the existing Secret from the
cluster. `helm template` has no cluster, so `lookup` returns nothing and each render generates a new password.

## Think like an engineer

Now let's see what Helm generates, and know what it **cannot** know:

| | `helm template` | `--dry-run=server` |
|---|---|---|
| cluster needed | no | yes |
| `.Capabilities`, `lookup` | defaults, empty | real |
| API validation | no | yes |

Use `helm template` in CI and reviews; `--dry-run=server` just before a real install. Never pipe `helm template`
into `kubectl apply` to "upgrade" a Helm release: you would bypass the release record, and for this chart you would
replace the database password.

## Checkpoint

- [ ] You can render one file of a chart, and a whole chart into a folder.
- [ ] You can explain why a `lookup`-based value differs between `helm template` and a real upgrade.
- [ ] You know which command validates against the API server without creating anything.

Next: [11 · Helm lint](11-helm-lint.md).
