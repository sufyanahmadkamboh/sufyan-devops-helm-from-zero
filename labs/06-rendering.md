# Lab 06 · Render and lint

> Level 8. Time: 30 minutes.

## Objective

Make rendering and linting a habit: see exactly what Helm will send to Kubernetes **before** it sends it, and let
`helm lint` find broken charts before a cluster does.

## Prerequisites

- [Lab 05](05-templates.md). The cluster (for the server-side check).

## Task

1. Render demo-app for an environment, all of it and one file at a time, and to a folder.
2. Know what `helm template` can and cannot know without a cluster.
3. Lint a chart with several mistakes, and read the report.

## Commands

### 1 · helm template

> Helm renders templates into normal Kubernetes YAML before Kubernetes receives them.

<!-- test: contains=kind: Deployment; output -->
```bash
helm template demo charts/demo-app -f charts/demo-app/values-dev.yaml --namespace demo-dev | grep -E '^(# Source|kind):'
```

```text
# Source: demo-app/templates/serviceaccount.yaml
kind: ServiceAccount
# Source: demo-app/templates/configmap.yaml
kind: ConfigMap
# Source: demo-app/templates/service.yaml
kind: Service
# Source: demo-app/templates/deployment.yaml
kind: Deployment
# Source: demo-app/templates/ingress.yaml
kind: Ingress
# Source: demo-app/templates/tests/test-connection.yaml
kind: Pod
```

Each object is preceded by `# Source:`, the template it came from. One file only:

<!-- test: contains=demo-dev.localhost; output=tail:16 -->
```bash
helm template demo charts/demo-app -f charts/demo-app/values-dev.yaml --show-only templates/ingress.yaml
```

```text
...
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/part-of: bookshop
    environment: "dev"
spec:
  ingressClassName: traefik
  rules:
    - host: "demo-dev.localhost"
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: demo-demo-app
                port:
                  number: 8080
```

Or every object as a file, the way you would review it or hand it to another tool:

<!-- test-run: rm -rf labs/work/rendered -->

<!-- test: contains=deployment.yaml; output -->
```bash
helm template demo charts/demo-app -f charts/demo-app/values-dev.yaml --output-dir labs/work/rendered > /dev/null
find labs/work/rendered -type f | sort
```

```text
labs/work/rendered/demo-app/templates/configmap.yaml
labs/work/rendered/demo-app/templates/deployment.yaml
labs/work/rendered/demo-app/templates/ingress.yaml
labs/work/rendered/demo-app/templates/service.yaml
labs/work/rendered/demo-app/templates/serviceaccount.yaml
labs/work/rendered/demo-app/templates/tests/test-connection.yaml
```

### 2 · What helm template does not know

`helm template` runs entirely on your computer: no cluster. So:

- `.Capabilities` is Helm's built-in default list, not your cluster's.
- `lookup` (read an object from the cluster) returns nothing.
- Nothing is validated against the Kubernetes API.

The bookshop chart uses `lookup` to keep its database password stable across upgrades
([secret.yaml](../charts/bookshop/templates/secret.yaml)). Without a cluster there is nothing to look up, so each
render generates a new random password:

<!-- test: output -->
```bash
helm dependency build charts/bookshop > /dev/null
for i in 1 2; do
  helm template shop charts/bookshop --show-only templates/secret.yaml | grep DB_PASSWORD
done
```

```text
  DB_PASSWORD: a0s2MDl1bjlPQ0FZYUJNRGNNbmVPN3R5
  DB_PASSWORD: YlRTczVEZE1QRHVjazJBZlhONmxTZHM1
```

Two different values: expected for `helm template`, and the reason you never apply `helm template` output to
upgrade a running release (the password would change under the database). For the real thing, `--dry-run=server`
renders with the cluster: real capabilities, real `lookup`, and the API server validates every object without
creating it:

<!-- test: contains=pending-install; output=head:6 -->
```bash
helm install demo charts/demo-app -f charts/demo-app/values-dev.yaml --namespace default --dry-run=server
```

```text
NAME: demo
LAST DEPLOYED: Sun Oct  4 23:25:31 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
...
```

| | `helm template` | `helm install --dry-run=server` |
|---|---|---|
| Needs a cluster | no | yes |
| Capabilities, `lookup` | defaults, empty | the real cluster |
| API validation | no | yes |
| Use it | in CI, in reviews, to learn | just before an install or upgrade |

### 3 · helm lint

`helm lint` loads the chart, renders it with the given values, and checks the result is YAML and well-formed
Kubernetes objects. Lint with each environment's values, since a mistake may only exist in one combination:

<!-- test: contains=0 chart(s) failed; absent=ERROR; output -->
```bash
for env in dev staging prod; do
  helm lint charts/demo-app -f charts/demo-app/values-$env.yaml | tail -1
done
```

```text
1 chart(s) linted, 0 chart(s) failed
1 chart(s) linted, 0 chart(s) failed
1 chart(s) linted, 0 chart(s) failed
```

`--strict` turns warnings into failures; CI pipelines often use it.

## Expected Output

- demo-app with dev values renders 6 objects (ServiceAccount, ConfigMap, Service, Deployment, Ingress, test Pod).
- Lint: `1 chart(s) linted, 0 chart(s) failed` for all three environments.

## Explanation

Render → lint → server dry-run → install. Each step catches a different class of problem:

```text
 helm template          template syntax, missing values, YAML structure        (no cluster, seconds)
 helm lint              + chart metadata, best-practice warnings               (no cluster, seconds)
 kubeconform (CI)       + strict Kubernetes schemas: unknown fields, types     (no cluster, seconds)
 --dry-run=server       + API validation, admission, real capabilities         (cluster, seconds)
 helm install           + everything that only fails at runtime: images, probes, config
```

The earlier a problem is caught, the cheaper it is. Rendering is also how you *review* a change: what will actually
be different in the cluster, not what the template diff suggests.

## Break It

A chart with three mistakes at once: a values file indented with a tab, a Chart.yaml with an invalid version, and a
template with an unclosed action.

<!-- test-run: rm -rf labs/work/lint-me && cp -r charts/demo-app labs/work/lint-me -->

<!-- test: fail; contains=found character that cannot start any token; output -->
```bash
printf 'service:\n\tport: 8080\n' >> labs/work/lint-me/values-dev.yaml
sed -i 's/^version: 1.0.0/version: latest/' labs/work/lint-me/Chart.yaml
sed -i 's/{{ .Values.containerPort }}/{{ .Values.containerPort }/' labs/work/lint-me/templates/deployment.yaml
helm lint labs/work/lint-me -f labs/work/lint-me/values-dev.yaml
```

```text
Error: failed to parse labs/work/lint-me/values-dev.yaml: cannot unmarshal yaml document: error converting YAML to JSON: yaml: line 12: found character that cannot start any token
```

One error, not three.

## Troubleshoot It

Lint reports the first thing that stops it, in this order: the values files (they are parsed first), then
`Chart.yaml` (the chart cannot load without it), then the templates. So the method is a loop: read the error, fix
it, lint again.

**Error 1**, the values file, line 12: `found character that cannot start any token`. That character is the tab:
YAML forbids tabs for indentation. Indent with spaces:

<!-- test: fail; contains=not a valid SemVer; output -->
```bash
sed -i 's/^\tport: 8080$/  port: 8080/' labs/work/lint-me/values-dev.yaml
helm lint labs/work/lint-me -f labs/work/lint-me/values-dev.yaml
```

```text
==> Linting labs/work/lint-me
[ERROR] Chart.yaml: version 'latest' is not a valid SemVer
[INFO] Chart.yaml: icon is recommended
[WARNING] Chart.yaml: version 'latest' is not a valid SemVerV2
[ERROR] templates/: validation: chart.metadata.version "latest" is invalid
[ERROR] : unable to load chart
	validation: chart.metadata.version "latest" is invalid

Error: 1 chart(s) linted, 1 chart(s) failed
```

**Error 2**, `Chart.yaml`: `version 'latest' is not a valid SemVer`. A chart version is always
`MAJOR.MINOR.PATCH`; "latest" is not a version, it is a moving pointer (and a repository could never serve two
different charts called "latest").

<!-- test: fail; contains=unexpected "}" in operand; output -->
```bash
sed -i 's/^version: latest/version: 1.0.0/' labs/work/lint-me/Chart.yaml
helm lint labs/work/lint-me -f labs/work/lint-me/values-dev.yaml
```

```text
==> Linting labs/work/lint-me
[INFO] Chart.yaml: icon is recommended
[ERROR] templates/: parse error at (demo-app/templates/deployment.yaml:47): unexpected "}" in operand

Error: 1 chart(s) linted, 1 chart(s) failed
```

**Error 3**, the template: file and line (`deployment.yaml:47`) and what the parser found: a `}` where it expected
`}}`.

<!-- test: contains=0 chart(s) failed; output -->
```bash
sed -i 's/{{ .Values.containerPort }$/{{ .Values.containerPort }}/' labs/work/lint-me/templates/deployment.yaml
helm lint labs/work/lint-me -f labs/work/lint-me/values-dev.yaml
```

```text
==> Linting labs/work/lint-me
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

## Challenge

Your team wants a "render check" for pull requests: one command that fails if the chart does not lint **or** does
not render for any of the three environments, and that writes the rendered production manifests to
`labs/work/prod-manifests/` for reviewers.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test-run: rm -rf labs/work/prod-manifests -->

<!-- test: contains=render check passed; output -->
```bash
set -e
for env in dev staging prod; do
  helm lint charts/demo-app -f charts/demo-app/values-$env.yaml --strict --quiet
  helm template demo charts/demo-app -f charts/demo-app/values-$env.yaml > /dev/null
done
helm template demo charts/demo-app -f charts/demo-app/values-prod.yaml --output-dir labs/work/prod-manifests > /dev/null
echo "render check passed"
```

```text
render check passed
```

`set -e` stops at the first failing command, so the script's exit code fails the pipeline. `--quiet` prints only
warnings and errors. This repository's CI ([test.yaml](../.github/workflows/test.yaml)) does the same for every chart,
plus kubeconform.

</details>

## Verification

<!-- test: contains=hpa.yaml -->
```bash
ls labs/work/prod-manifests/demo-app/templates/
```

## Cleanup

<!-- test -->
```bash
rm -rf labs/work/rendered labs/work/lint-me labs/work/prod-manifests
```

Next: [lab 07 · Install a release](07-install-release.md).
