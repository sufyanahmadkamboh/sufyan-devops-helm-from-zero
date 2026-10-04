# Charts and Chart.yaml

> Hands-on: [lab 02](../labs/02-first-chart.md), [lab 03](../labs/03-chart-structure.md).

## 1 · What is it?

A **chart** is a folder (or a `.tgz` of that folder) that describes a Kubernetes application:

```text
demo-app/
├── Chart.yaml        identity: name, versions, description, dependencies
├── values.yaml       the settings, with defaults
├── values-*.yaml     (convention) one file per environment
├── charts/           dependencies, downloaded
├── templates/        manifests with placeholders, helpers, NOTES.txt, tests/
├── values.schema.json  (optional) rules the values must follow
├── README.md         (optional) shown by helm show readme
└── .helmignore       files left out of the package
```

`Chart.yaml` is its identity card:

```yaml
apiVersion: v2          # chart format (Helm 3 and 4), not a Kubernetes API version
name: demo-app          # the chart's name: package name, default resource names, the app.kubernetes.io/name label
description: The Bookshop frontend ...
type: application       # or "library": helpers only, cannot be installed
version: 1.0.0          # the CHART's version (SemVer)
appVersion: "1.0.0"     # the APPLICATION's version: the default image tag
```

## 2 · Why do we need it?

To ship an application as one versioned unit instead of a folder of loose YAML: something you can install, upgrade,
roll back, publish and depend on, by name and version.

## 3 · How does it work?

Helm loads the folder (or archive), reads `Chart.yaml`, merges `values.yaml` with your values, renders `templates/`,
and sends the result to Kubernetes. `helm package` turns the folder into `NAME-VERSION.tgz`, named from `Chart.yaml`.

## 4 · What problem does it solve?

Copies. One chart serves every environment and every team that installs it.

## 5 · How do I use it?

Start with `helm create NAME` (conventional skeleton) or an empty folder with `Chart.yaml` + `templates/`
([challenge 1](../challenges/README.md#challenge-1--create-a-chart-from-scratch)). Adapt templates to the application,
put every setting that varies into `values.yaml`.

## 6 · What command should I run?

```bash
helm create my-app                  # skeleton
helm show chart charts/demo-app     # read Chart.yaml of any chart (folder, .tgz, repo, oci://)
helm lint charts/demo-app           # validate
helm package charts/demo-app        # → demo-app-1.0.0.tgz
helm package charts/demo-app --version 1.0.1 --app-version 1.1.0   # set versions at package time (CI)
```

## 7 · What output should I expect?

`helm show chart` prints `Chart.yaml`; `helm package` prints `Successfully packaged chart and saved it to: ...`.

## 8 · What can go wrong?

| Problem | Symptom |
|---|---|
| Missing `name` / `version` | lint: `name is required`, `version ... is not a valid SemVer` |
| Unquoted `appVersion: 1.10` | becomes the number 1.1; lint error, wrong image tag ([lab 03](../labs/03-chart-structure.md#break-it)) |
| Contents changed, version not | two different packages called `demo-app-1.0.0.tgz`: users cannot trust versions |
| `type: library` | `helm install` refuses: library charts are not installable |

## 9 · How do I troubleshoot it?

`helm lint` first; `helm show chart` to see what Helm actually parsed; `tar -tzf NAME.tgz` to see what a package
contains (and whether `.helmignore` excluded the right files).

## 10 · Where is it used in real DevOps work?

Every application deployed with Helm has one: per service, or one shared chart for many similar services. Platform
teams maintain charts for internal tools; vendors ship charts for their software.

## Chart version vs application version

| | Chart version (`version`) | Application version (`appVersion`) |
|---|---|---|
| Describes | the package: templates, defaults, options | the software deployed |
| Changes when | anything in the chart changes | the developers release |
| Format | SemVer, required | free text (quote it), usually SemVer |
| Seen in | `helm list` → `CHART demo-app-1.0.0`, package file names | `helm list` → `APP VERSION`, image tags |
| Example | `1.2.0` → `1.3.0`: new PDB option | `1.0.0` → `2.0.0`: new release of the app |

They move independently, but a new `appVersion` changes the package's contents, so it also means a new chart
version. Real-world example: chart `1.2.0` deploying application `2.0.0`.
