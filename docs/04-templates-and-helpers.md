# Templates, helpers and labels

> Hands-on: [lab 05](../labs/05-templates.md), [lab 14](../labs/14-tests.md#4--helpers-keep-labels-consistent),
> [examples/basic-chart](../examples/basic-chart).

## 1 · What is it?

Kubernetes manifests with Go-template placeholders, in `templates/`. **Helpers** are named templates
(`{{ define "name" }}`) in files starting with `_` (usually `_helpers.tpl`), reused with `include`.

## 2 · Why do we need it?

To write a manifest once and let values fill in what differs; helpers to write shared pieces (names, labels) once.

## 3 · How does it work?

Helm renders each file as **text** with the values and built-in objects, then parses the text as YAML.

| Object | Contains |
|---|---|
| `.Values` | the merged values |
| `.Release` | `Name`, `Namespace`, `Revision`, `IsInstall`, `IsUpgrade`, `Service` |
| `.Chart` | fields of `Chart.yaml` (`Name`, `Version`, `AppVersion`) |
| `.Capabilities` | the cluster's Kubernetes version and APIs |
| `.Template` | the current template's name and base path |

The constructs this course uses: `{{ }}`, `if/else`, `range`, `with`, `define/include`, and the functions `default`,
`quote`, `toYaml`, `nindent`, `required`, `tpl`, `sha256sum`, `lookup`, `fail`, `dict`, `printf`, `trunc`.
[examples/basic-chart](../examples/basic-chart) uses each one, with a comment.

## 4 · What problem does it solve?

Duplication inside a chart (five services from one template in [bookshop](../charts/bookshop)) and inconsistency
(every object gets the same labels from one helper).

## 5 · How do I use it?

Keep templates close to plain Kubernetes YAML; add logic only where values must change the output; move repeated
fragments into helpers; render after every change.

## 6 · What command should I run?

```bash
helm template demo charts/demo-app --show-only templates/deployment.yaml
helm template demo charts/demo-app --debug          # renders even invalid YAML, to see it
```

## 7 · What output should I expect?

Plain YAML, each document preceded by `# Source: <chart>/templates/<file>`.

## 8 · What can go wrong?

| Error | Cause |
|---|---|
| `unexpected EOF` | an `if/range/with/define` without `end` ([01](../troubleshooting/01-template-syntax-error.md)) |
| `YAML parse error` | wrong indentation in the output; check `nindent` |
| valid YAML, wrong structure | wrong `nindent` that still parses ([lab 05](../labs/05-templates.md#break-it)) |
| `nil pointer evaluating` | a parent key is missing (`.Values.a.b` with no `a`) |
| `error calling include: template: no template "x"` | helper name typo |

## 9 · How do I troubleshoot it?

`helm lint`, `helm template --debug`, `--show-only` the file in question, and a strict schema check
(`helm template ... | kubeconform -strict`).

## 10 · Where is it used in real DevOps work?

Avoiding duplicated Kubernetes YAML: every chart, every day. Reading templates is also how you review third-party
charts.

## Labels: why consistent metadata matters

The helper `bookshop.labels` gives every object `app.kubernetes.io/name`, `instance`, `version`, `managed-by`,
`helm.sh/chart` and `environment`. That serves:

| Need | How labels help |
|---|---|
| Kubernetes operations | Services and Deployments find Pods by `name` + `instance` |
| Debugging | `kubectl get all -l app.kubernetes.io/instance=shop` shows one release, all kinds |
| Monitoring | dashboards and alerts group by `name`, `version`, `environment` |
| Organisation | costs per `environment`, ownership audits via `managed-by` |

Keep **selector** labels (name + instance) in their own helper and never change them: a Deployment's selector is
immutable ([troubleshooting 04](../troubleshooting/04-wrong-service-selector.md)).
