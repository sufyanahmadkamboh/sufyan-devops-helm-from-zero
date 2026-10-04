# Chapter 07 · Chart.yaml

> Lesson: [lab 03](../labs/03-chart-structure.md), section 5 to the end. Time: 20 minutes.

## Do

Package demo-app twice (`1.0.0`, then `--version 1.0.1 --app-version 1.1.0`), inspect the package, then the Break It
(an unquoted `appVersion: 1.10`) and the challenge.

## Watch for

```text
name: demo-app
version: 1.0.1
appVersion: 1.1.0
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.1.0"
```

and the Break It:

```text
[ERROR] Chart.yaml: appVersion should be of type string but it's of type float64
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.1"
```

## Think like an engineer

`1.10` became `1.1`: YAML guessed a number. That image tag might not exist, or worse, it might be a different, older
version. Quote anything that looks like a number but is a string: versions, tags, zip codes, `"true"`.

The versioning table in the lab is the one to remember:

```text
 frontend 1.1.0 released      chart 1.0.0 → 1.0.1   app 1.0.0 → 1.1.0
 chart gets a PDB option      chart 1.0.1 → 1.1.0   app stays 1.1.0
 a value is renamed           chart 1.1.0 → 2.0.0   (breaking for chart users)
```

## Checkpoint

- [ ] You can produce a package with any chart/app version without editing `Chart.yaml`.
- [ ] You know why a published chart version must never be re-published with different contents.
- [ ] You can exclude a file from a package with `.helmignore`.

Next: [08 · values.yaml](08-values.md).
