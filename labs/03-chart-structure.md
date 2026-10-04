# Lab 03 · Chart structure, Chart.yaml, chart version vs app version

> Level 5. Time: 30 minutes. No cluster needed.

## Objective

Read a real chart file by file: [charts/demo-app](../charts/demo-app), the Bookshop frontend packaged with Helm.
Understand what every file is for, how `helm create`'s scaffold became this chart, and the difference between the
**chart version** and the **application version**.

## Prerequisites

- [Lab 02](02-first-chart.md) (you have seen `helm create`).

## Task

1. Inspect the chart with `helm show`, the way you would inspect a chart from another team.
2. Find what was changed compared with the scaffold.
3. Package the chart twice: with its own versions, and as a new chart version with a new application version.

## Commands

### 1 · The chart's identity: Chart.yaml

<!-- test: contains=appVersion; output -->
```bash
cat charts/demo-app/Chart.yaml
```

```text
apiVersion: v2                 # chart API version 2 (Helm 3 and 4)
name: demo-app
description: The Bookshop frontend (React, served by nginx), packaged as a Helm chart. The chart of the Helm lessons.
type: application              # an installable application (the other type, "library", only holds helpers)

# The version of the CHART: change it whenever the chart (templates, values, this file) changes. Semantic versioning.
version: 1.0.0

# The version of the APPLICATION the chart deploys by default: the image tag, unless values override it.
appVersion: "1.0.0"

keywords: [bookshop, frontend, react, nginx, example]
home: https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero
sources:
  - https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes/tree/main/applications/frontend
maintainers:
  - name: Sufyan Ahmad
```

| Field | Meaning |
|---|---|
| `apiVersion: v2` | The chart format (v2 = Helm 3 and 4). Not a Kubernetes apiVersion |
| `name` | The chart's name; also the default for resource names and the `app.kubernetes.io/name` label |
| `description` | One line, shown by `helm search` |
| `type` | `application` (installable) or `library` (only helpers for other charts) |
| `version` | **The chart's version**: SemVer, changes with every change to the chart |
| `appVersion` | **The application's version**: here the image tag deployed by default. A string: quote it |
| `keywords`, `home`, `sources`, `maintainers` | Metadata for people and for repositories |

### 2 · Inspect it like a consumer

You will mostly install charts written by other people. Before installing, read them. `helm show` works on a folder, a
packaged `.tgz`, a repository chart or an OCI reference:

<!-- test: contains=version: 1.0.0; output -->
```bash
helm show chart charts/demo-app
```

```text
apiVersion: v2
appVersion: 1.0.0
description: The Bookshop frontend (React, served by nginx), packaged as a Helm chart.
  The chart of the Helm lessons.
home: https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero
keywords:
- bookshop
- frontend
- react
- nginx
- example
maintainers:
- name: Sufyan Ahmad
name: demo-app
sources:
- https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes/tree/main/applications/frontend
type: application
version: 1.0.0
```

<!-- test: contains=replicaCount; output=head:25 -->
```bash
helm show values charts/demo-app
```

```text
# Default values for demo-app. Every value can be overridden per environment (values-dev.yaml, ...) or per install
# (-f my-values.yaml, --set key=value). Values files hold configuration, NEVER real secrets.

# How many Pods. Ignored when autoscaling.enabled is true (the HorizontalPodAutoscaler decides then).
replicaCount: 1

image:
  repository: ghcr.io/sufyanahmadkamboh/bookshop-frontend
  # Empty = use the chart's appVersion (Chart.yaml). Set it to deploy another application version.
  tag: ""
  pullPolicy: IfNotPresent

# Which environment this release is. Shown in the UI footer, added as a label to every resource.
environment: local

# Application configuration, rendered into a ConfigMap (templates/configmap.yaml).
config:
  adminUrl: ""                 # the "Reviews admin" link of the UI (empty = hidden)

# The port the container listens on (the nginx inside the image listens on 8080).
containerPort: 8080

service:
  type: ClusterIP
  port: 8080                   # the port of the Service (what other Pods and the Ingress call)
...
```

<!-- test: contains=# demo-app; output=head:12 -->
```bash
helm show readme charts/demo-app
```

```text
# demo-app

The Bookshop frontend (a React app served by nginx) as a Helm chart: the chart of the course's lessons.
Image: `ghcr.io/sufyanahmadkamboh/bookshop-frontend`, listening on port 8080, health check on `/health`, its
environment shown at `/config.js` and in the page footer.

| | |
|---|---|
| Chart version | `1.0.0` (the version of this package) |
| App version | `1.0.0` (the image tag deployed unless `image.tag` is set) |

## Install
...
```

`helm show all` prints the three together. These three outputs are the chart's interface: what it is, what you can
configure, and how the author tells you to use it.

### 3 · The templates

<!-- test: contains=configmap.yaml; output -->
```bash
ls -A charts/demo-app charts/demo-app/templates charts/demo-app/templates/tests
```

```text
charts/demo-app:
.helmignore
Chart.yaml
README.md
charts
templates
values-dev.yaml
values-prod.yaml
values-staging.yaml
values.yaml

charts/demo-app/templates:
NOTES.txt
_helpers.tpl
configmap.yaml
deployment.yaml
hpa.yaml
httproute.yaml
ingress.yaml
service.yaml
serviceaccount.yaml
tests

charts/demo-app/templates/tests:
test-connection.yaml
```

| File | Purpose in demo-app |
|---|---|
| `deployment.yaml` | The frontend Pods: image, port 8080, probes on `/health`, resources, security context |
| `service.yaml` | ClusterIP Service on 8080 |
| `configmap.yaml` | **Added:** `APP_ENV` and `ADMIN_URL`, read by the app |
| `ingress.yaml` | Host-based routing through Traefik when `ingress.enabled` |
| `hpa.yaml` | Autoscaling when `autoscaling.enabled` (production) |
| `serviceaccount.yaml` | A dedicated identity, with the API token not mounted (`automount: false`) |
| `httproute.yaml` | Gateway API alternative to the Ingress, off |
| `_helpers.tpl` | Named templates: `demo-app.fullname`, `demo-app.labels` (**added:** `environment`, `part-of`), ... |
| `NOTES.txt` | **Rewritten:** versions, environment, URL, how to check |
| `tests/test-connection.yaml` | **Rewritten:** checks `/health` and that the right environment reached the app |
| `../.helmignore` | Files left out of the package |
| `../values*.yaml` | Defaults + one file per environment (lab 10) |

The named templates in `_helpers.tpl`:

<!-- test: contains=demo-app.labels; output -->
```bash
grep -n 'define' charts/demo-app/templates/_helpers.tpl
```

```text
4:{{- define "demo-app.name" -}}
13:{{- define "demo-app.fullname" -}}
29:{{- define "demo-app.chart" -}}
36:{{- define "demo-app.labels" -}}
50:{{- define "demo-app.selectorLabels" -}}
58:{{- define "demo-app.serviceAccountName" -}}
```

### 4 · From scaffold to chart

What exactly was changed in the Deployment? Generate a fresh scaffold with the same name and compare:

<!-- test-run: rm -rf labs/work/scaffold -->

<!-- test: contains=checksum/config; contains=envFrom; output -->
```bash
mkdir -p labs/work/scaffold
helm create labs/work/scaffold/demo-app > /dev/null
diff labs/work/scaffold/demo-app/templates/deployment.yaml charts/demo-app/templates/deployment.yaml || true
```

```text
16d15
<       {{- with .Values.podAnnotations }}
17a17,19
>         # a hash of the ConfigMap: when the configuration changes, the Pod template changes, so the Pods are replaced
>         checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
>         {{- with .Values.podAnnotations }}
19c21
<       {{- end }}
---
>         {{- end }}
45c47
<               containerPort: {{ .Values.service.port }}
---
>               containerPort: {{ .Values.containerPort }}
46a49,51
>           envFrom:
>             - configMapRef:
>                 name: {{ include "demo-app.fullname" . }}
```

Three changes, each with a reason:

- `checksum/config`: a hash of the rendered ConfigMap as a Pod annotation. Change the configuration → the hash
  changes → the Pod template changes → Kubernetes rolls the Pods. Without it, a changed ConfigMap does not restart
  anything, and the Pods keep the old environment variables.
- `containerPort: {{ .Values.containerPort }}`: the scaffold reused `service.port` for the container; separating them
  lets the Service port differ from what the app listens on.
- `envFrom` the ConfigMap: the configuration reaches the container.

### 5 · Chart version vs application version

Package the chart: a `.tgz` named after the chart and its **chart** version.

<!-- test: contains=demo-app-1.0.0.tgz; output -->
```bash
helm package charts/demo-app --destination labs/work
```

```text
Successfully packaged chart and saved it to: labs\work\demo-app-1.0.0.tgz
```

Now two release situations. The application team ships the frontend `1.1.0`; the chart's contents change (new
default image), so the chart gets a new version too, `1.0.1`. `helm package` can set both without editing the file,
which is how CI pipelines usually do it:

<!-- test: contains=demo-app-1.0.1.tgz; output -->
```bash
helm package charts/demo-app --version 1.0.1 --app-version 1.1.0 --destination labs/work
ls labs/work/*.tgz
```

```text
Successfully packaged chart and saved it to: labs\work\demo-app-1.0.1.tgz
labs/work/demo-app-1.0.0.tgz
labs/work/demo-app-1.0.1.tgz
```

<!-- test: contains=appVersion: 1.1.0; output -->
```bash
helm show chart labs/work/demo-app-1.0.1.tgz | grep -E '^(name|version|appVersion)'
helm template demo labs/work/demo-app-1.0.1.tgz --show-only templates/deployment.yaml | grep 'image:'
```

```text
appVersion: 1.1.0
name: demo-app
version: 1.0.1
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.1.0"
```

Same templates, a new application version: the image tag follows `appVersion`. And the reverse case: you add a
template option (say, a PodDisruptionBudget) without changing the app: chart `1.0.1 → 1.1.0`, app stays `1.1.0`.

```text
                         chart version (package)     app version (image)
 initial release               1.0.0                       1.0.0
 frontend 1.1.0 released       1.0.1                       1.1.0     ← app changed → chart contents changed
 chart gets a PDB option       1.1.0                       1.1.0     ← chart feature, same app
```

What is inside a package?

<!-- test: contains=demo-app/Chart.yaml; output -->
```bash
tar -tzf labs/work/demo-app-1.0.0.tgz | sort
```

```text
demo-app/.helmignore
demo-app/Chart.yaml
demo-app/README.md
demo-app/templates/NOTES.txt
demo-app/templates/_helpers.tpl
demo-app/templates/configmap.yaml
demo-app/templates/deployment.yaml
demo-app/templates/hpa.yaml
demo-app/templates/httproute.yaml
demo-app/templates/ingress.yaml
demo-app/templates/service.yaml
demo-app/templates/serviceaccount.yaml
demo-app/templates/tests/test-connection.yaml
demo-app/values-dev.yaml
demo-app/values-prod.yaml
demo-app/values-staging.yaml
demo-app/values.yaml
```

The chart folder, minus what `.helmignore` excludes. A `.tgz` is what repositories serve (lab 11).

## Expected Output

- `helm show chart`: `version: 1.0.0`, `appVersion: 1.0.0`.
- Two packages: `demo-app-1.0.0.tgz` and `demo-app-1.0.1.tgz`; the second renders `bookshop-frontend:1.1.0`.

## Explanation

The chart version answers "which **package** is this?"; the app version answers "which **software** does it deploy
by default?". They move independently, and the chart version must change whenever the package's contents do:
a repository can only ever have one `demo-app-1.0.1.tgz`, and users who pinned it rely on it never changing.

`helm list` shows both columns (`CHART demo-app-1.0.0`, `APP VERSION 1.0.0`): when someone asks "which version is
running?", the answer has two numbers.

## Break It

YAML guesses types. A version like `1.10` without quotes is a number:

<!-- test-run: rm -rf labs/work/broken && cp -r charts/demo-app labs/work/broken -->

<!-- test: fail; contains=appVersion should be of type string; output -->
```bash
sed -i.bak 's/^appVersion: "1.0.0"/appVersion: 1.10/' labs/work/broken/Chart.yaml
helm lint labs/work/broken
```

```text
==> Linting labs/work/broken
[ERROR] Chart.yaml: appVersion should be of type string but it's of type float64
[INFO] Chart.yaml: icon is recommended

Error: 1 chart(s) linted, 1 chart(s) failed
```

## Troubleshoot It

What would it have deployed?

<!-- test: contains=bookshop-frontend:1.1"; output -->
```bash
helm template demo labs/work/broken --show-only templates/deployment.yaml | grep 'image:'
```

```text
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.1"
```

`1.10` became the number `1.1`: an image tag that does not exist, or worse, another version that does. The rule:
quote versions, tags, anything that looks like a number but is a string (`"1.10"`, `"08"`, `"true"`). Fix:

<!-- test: contains=0 chart(s) failed -->
```bash
sed -i 's/^appVersion: 1.10/appVersion: "1.10"/' labs/work/broken/Chart.yaml
helm lint labs/work/broken
```

## Challenge

1. Package the chart as chart `2.0.0` with app version `1.0.0`. Which situation would justify a new **major**
   chart version while the application did not change?
2. Exclude the file `README.md` from the package and verify it is gone.

## Solution

<details>
<summary>Open the solution</summary>

A major chart version signals a breaking change for chart users: a renamed value (`replicaCount` → `replicas`),
removed options, a changed selector (which forces a reinstall). The application can be identical.

<!-- test: contains=demo-app-2.0.0.tgz; absent=README.md; output -->
```bash
cp -r charts/demo-app labs/work/pkg
echo 'README.md' >> labs/work/pkg/.helmignore
helm package labs/work/pkg --version 2.0.0 --destination labs/work
tar -tzf labs/work/demo-app-2.0.0.tgz | sort
```

```text
Successfully packaged chart and saved it to: labs\work\demo-app-2.0.0.tgz
demo-app/.helmignore
demo-app/Chart.yaml
demo-app/templates/NOTES.txt
demo-app/templates/_helpers.tpl
demo-app/templates/configmap.yaml
demo-app/templates/deployment.yaml
demo-app/templates/hpa.yaml
demo-app/templates/httproute.yaml
demo-app/templates/ingress.yaml
demo-app/templates/service.yaml
demo-app/templates/serviceaccount.yaml
demo-app/templates/tests/test-connection.yaml
demo-app/values-dev.yaml
demo-app/values-prod.yaml
demo-app/values-staging.yaml
demo-app/values.yaml
```

The package is named after the `name` in Chart.yaml (`demo-app`), not after the folder (`pkg`).

</details>

## Verification

<!-- test: contains=0 chart(s) failed; contains=demo-app-1.0.0.tgz -->
```bash
helm lint charts/demo-app
ls labs/work/
```

## Cleanup

<!-- test: absent=tgz -->
```bash
rm -rf labs/work/scaffold labs/work/broken labs/work/pkg labs/work/*.tgz
ls labs/work/
```

Next: [lab 04 · Values](04-values.md).
