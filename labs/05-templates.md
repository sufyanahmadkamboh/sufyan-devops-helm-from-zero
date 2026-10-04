# Lab 05 · Templates

> Level 7. Time: 40 minutes.

## Objective

Read and write Helm templates: the Go-template syntax and the dozen functions this repository actually uses. Each
one is used once in [examples/basic-chart](../examples/basic-chart), with a comment where it is used.

## Prerequisites

- [Lab 04](04-values.md). The cluster (for the last steps).

## Task

1. Render basic-chart and match each output line to the construct that produced it.
2. Change values and watch the output change.
3. Break a template in two ways and read Helm's errors.

## Commands

### The syntax in one table

| Construct | Example from basic-chart | Renders |
|---|---|---|
| `{{ }}` | `replicas: {{ .Values.replicaCount }}` | `replicas: 2` |
| `.Values` | `.Values.image.repository` | from values.yaml / `-f` / `--set` |
| `.Release` | `{{ .Release.Name }} rev {{ .Release.Revision }}` | `web rev 1` |
| `.Chart` | `{{ .Chart.Name }}`, `.Chart.AppVersion` | `basic-chart`, `1.0.0` |
| `.Capabilities` | `.Capabilities.APIVersions.Has "networking.k8s.io/v1"` | true if the cluster serves that API |
| `if` / `else` | `if eq .Values.environment "prod"` | one branch or the other |
| `range` | `range $key, $value := .Values.config` | one line per map entry |
| `with` | `with .Values.ingress.host` | the block, with `.` = the value, only if set |
| `default` | `.Values.image.tag \| default .Chart.AppVersion` | the tag, or appVersion if empty |
| `quote` | `.Values.environment \| quote` | `"dev"`: always a string |
| `toYaml` | `toYaml .Values.resources` | a whole map as YAML |
| `nindent N` | `\| nindent 12` | newline + indent every line by N |
| `include` | `include "basic.labels" .` | the output of a named template |
| `{{-` / `-}}` | `{{- if ... }}` | trim whitespace (newlines) before / after |

`|` is a **pipe**: the value on the left becomes the last argument of the function on the right.
`.Values.environment | quote` is `quote .Values.environment`.

### Render and read

<!-- test: contains=replicas: 2; contains=value: "web rev 1 in lab-05"; output -->
```bash
helm template web examples/basic-chart --namespace lab-05 --show-only templates/deployment.yaml
```

```text
---
# Source: basic-chart/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  # include: insert a named template from _helpers.tpl
  name: web
  labels:
    # nindent 4: a new line, then indent every line by 4 spaces (YAML is indentation-sensitive)
    app.kubernetes.io/name: basic-chart
    app.kubernetes.io/instance: web
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
    helm.sh/chart: basic-chart-0.1.0
    environment: "dev"
    team: web
spec:
  # .Values: anything from values.yaml, -f files or --set
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: basic-chart
      app.kubernetes.io/instance: web
  template:
    metadata:
      labels:
        # the Pods get all labels (the selector labels are among them), so you can filter Pods by environment
        app.kubernetes.io/name: basic-chart
        app.kubernetes.io/instance: web
        app.kubernetes.io/version: "1.0.0"
        app.kubernetes.io/managed-by: Helm
        helm.sh/chart: basic-chart-0.1.0
        environment: "dev"
        team: web
    spec:
      containers:
        # .Chart: the fields of Chart.yaml (here its name)
        - name: basic-chart
          # default: use the tag if set, otherwise the chart's appVersion
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0"
          ports:
            - containerPort: 8080
          env:
            # quote: always a YAML string ("dev"), even for values like 1.10 or true
            - name: APP_ENV
              value: "dev"
            # .Release: facts about this install (name, namespace, revision, IsInstall, IsUpgrade)
            - name: RELEASE
              value: "web rev 1 in lab-05"
          imagePullPolicy: IfNotPresent
          # toYaml: a whole map from values, written as YAML (here the resources block)
          resources:
            requests:
              cpu: 10m
              memory: 32Mi
```

Line by line, against [the template](../examples/basic-chart/templates/deployment.yaml):

- `name: web`: `include "basic.fullname" .` → the release name.
- The labels block: `include "basic.labels" . | nindent 4`. `basic.labels` itself includes the selector labels,
  adds the version (`default`), the environment (`quote`), and `team: web` from `extraLabels` (`with` + `toYaml`).
- `image:`: `repository` + `:` + (`tag` or `appVersion`).
- `value: "web rev 1 in lab-05"`: `.Release.Name`, `.Release.Revision`, `.Release.Namespace`.
- `imagePullPolicy: IfNotPresent`: the `else` branch, because environment is `dev`.
- `resources:`: `toYaml .Values.resources | nindent 12`.

### Change values, watch the output

`if/else` with `environment=prod`:

<!-- test: contains=imagePullPolicy: Always; output -->
```bash
helm template web examples/basic-chart --set environment=prod --show-only templates/deployment.yaml | grep -E 'environment|imagePullPolicy'
```

```text
    environment: "prod"
        # the Pods get all labels (the selector labels are among them), so you can filter Pods by environment
        environment: "prod"
          imagePullPolicy: Always
```

`range` over a map: add a key, get a line, no template change:

<!-- test: contains=CACHE_TTL: "300"; output=tail:4 -->
```bash
helm template web examples/basic-chart --set config.CACHE_TTL=300 --show-only templates/configmap.yaml
```

```text
...
data:
  CACHE_TTL: "300"
  FEATURE_REVIEWS: "true"
  LOG_LEVEL: "info"
```

`range` visits map keys in alphabetical order, so the output is stable from one render to the next (no false
"changes" in a diff). `quote` turned the number `300` into the string `"300"` that a ConfigMap requires.

`with` + `if` + `.Capabilities`: the Ingress exists only when enabled; the host only when set:

<!-- test: contains=host: "basic.localhost"; output=tail:6 -->
```bash
helm template web examples/basic-chart --set ingress.enabled=true --show-only templates/ingress.yaml
```

```text
...
              service:
                name: web
                port:
                  number: 8080
      # with: if the value is set, run the block with "." = that value. No host = a rule for every host name.
      host: "basic.localhost"
```

<!-- test: fail; contains=could not find template; output -->
```bash
helm template web examples/basic-chart --show-only templates/ingress.yaml
```

```text
Error: could not find template templates/ingress.yaml in chart
```

With `ingress.enabled=false` the whole file renders to nothing, and there is no Ingress to show.

### See every value a template can use

`.Release`, `.Chart` and `.Capabilities` are filled by Helm. With a cluster, `--dry-run=server` asks the API server,
so `.Capabilities` reflects the real cluster, and Kubernetes validates every object without creating it:

<!-- test: contains=STATUS: pending-install; output=head:8 -->
```bash
kubectl create namespace lab-05 --dry-run=client -o yaml | kubectl apply -f - > /dev/null
helm install web examples/basic-chart --namespace lab-05 --dry-run=server --set ingress.enabled=true
```

```text
NAME: web
LAST DEPLOYED: Mon Oct  5 00:59:30 2026
NAMESPACE: lab-05
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
HOOKS:
...
```

`pending-install` + no error: every rendered object was accepted by the API server. Nothing was created.

## Expected Output

- Default render: `replicas: 2`, image `bookshop-frontend:1.0.0`, labels including `environment: "dev"` and `team: web`.
- `environment=prod` → `imagePullPolicy: Always`.

## Explanation

A Helm template is a text template, not a YAML-aware one. Helm produces **text**, then parses it as YAML. Two
consequences:

1. **Indentation is your job.** `include` returns text without indentation; `nindent` adds it. The wrong number gives
   valid template syntax and invalid (or, worse, valid but different) YAML.
2. **Types are your job.** `{{ .Values.environment }}` with the value `true` renders `value: true`: a YAML boolean.
   `quote` makes it `"true"`. Kubernetes requires strings in env values, labels and ConfigMap data.

`{{-` removes the whitespace and newline **before** the tag, `-}}` the ones after. Without them, every `if` and
`end` would leave an empty line behind.

## Break It

Two classic mistakes, in a copy of the chart. First, a forgotten `end`:

<!-- test-run: rm -rf labs/work/tpl && mkdir -p labs/work && cp -r examples/basic-chart labs/work/tpl -->

<!-- test: fail; contains=unexpected EOF; output -->
```bash
sed -i.bak '/{{- end }}/d' labs/work/tpl/templates/configmap.yaml
helm template web labs/work/tpl
```

```text
Error: parse error at (basic-chart/templates/configmap.yaml:11): unexpected EOF

Use --debug flag to render out invalid YAML
```

Second, wrong indentation: restore the first file, then indent the labels by 2 instead of 4.

<!-- test: contains=kind: Deployment -->
```bash
mv labs/work/tpl/templates/configmap.yaml.bak labs/work/tpl/templates/configmap.yaml
sed -i 's/include "basic.labels" . | nindent 4/include "basic.labels" . | nindent 2/' labs/work/tpl/templates/deployment.yaml
helm lint labs/work/tpl | tail -1
helm template web labs/work/tpl | grep kind:
```

No error at all: lint passes, rendering works. And the API server agrees:

<!-- test: contains=STATUS: pending-install -->
```bash
helm install web labs/work/tpl --namespace lab-05 --dry-run=server | grep STATUS
```

## Troubleshoot It

- `unexpected EOF`: the template parser reached the end of `configmap.yaml` with a block still open. Count `range`,
  `if`, `with`, `define` against `end`. The message gives the file and the line where parsing stopped.
- The indentation mistake is the dangerous one: no tool complained. **Don't trust the template just because Helm
  accepted it: render it and read it.**

<!-- test: contains=  app.kubernetes.io/name: basic-chart; output -->
```bash
helm template web labs/work/tpl --show-only templates/deployment.yaml | sed -n '/^metadata:/,/^spec:/p'
```

```text
metadata:
  # include: insert a named template from _helpers.tpl
  name: web
  labels:
    # nindent 4: a new line, then indent every line by 4 spaces (YAML is indentation-sensitive)
  app.kubernetes.io/name: basic-chart
  app.kubernetes.io/instance: web
  app.kubernetes.io/version: "1.0.0"
  app.kubernetes.io/managed-by: Helm
  helm.sh/chart: basic-chart-0.1.0
  environment: "dev"
  team: web
spec:
```

The labels are no longer under `labels:` (which is now empty) but directly under `metadata:`, as fields Kubernetes
does not know. The API server silently drops unknown fields here, so the Deployment would be created **without
labels**: no `environment`, no `team`, nothing for monitoring or `kubectl get -l` to select on.

A strict schema validator catches it. This repository's CI renders every chart through
[kubeconform](https://github.com/yannh/kubeconform) for exactly this reason (install it to try):

<!-- test: skip -->
```bash
helm template web labs/work/tpl | kubeconform -strict -summary
```

```text
stdin - Deployment web is invalid: ... at '/metadata': additional properties 'app.kubernetes.io/name', 'environment', ... not allowed
Summary: 3 resources found parsing stdin - Valid: 2, Invalid: 1, Errors: 0, Skipped: 0
```

Fix the number and check the result:

<!-- test: contains=    app.kubernetes.io/name: basic-chart -->
```bash
sed -i 's/include "basic.labels" . | nindent 2/include "basic.labels" . | nindent 4/' labs/work/tpl/templates/deployment.yaml
helm template web labs/work/tpl --show-only templates/deployment.yaml | sed -n '/^metadata:/,/^spec:/p'
```

## Challenge

Add a template to `labs/work/tpl`: a PodDisruptionBudget that keeps at least one Pod running during node maintenance,
rendered **only when `replicaCount` is greater than 1** (with one replica, `minAvailable: 1` would block every node
drain). Reuse the selector-labels helper. Check it with 1 and 3 replicas.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: contains=kind: PodDisruptionBudget; contains=app.kubernetes.io/instance: web; output -->
```bash
cat > labs/work/tpl/templates/pdb.yaml <<'EOF'
{{- if gt (int .Values.replicaCount) 1 }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "basic.fullname" . }}
  labels:
    {{- include "basic.labels" . | nindent 4 }}
spec:
  minAvailable: 1
  selector:
    matchLabels:
      {{- include "basic.selectorLabels" . | nindent 6 }}
{{- end }}
EOF
helm template web labs/work/tpl --set replicaCount=3 --show-only templates/pdb.yaml
```

```text
---
# Source: basic-chart/templates/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web
  labels:
    app.kubernetes.io/name: basic-chart
    app.kubernetes.io/instance: web
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
    helm.sh/chart: basic-chart-0.1.0
    environment: "dev"
    team: web
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: basic-chart
      app.kubernetes.io/instance: web
```

<!-- test: fail; contains=could not find template -->
```bash
helm template web labs/work/tpl --set replicaCount=1 --show-only templates/pdb.yaml
```

`gt` compares two numbers; `int` converts first, because `--set replicaCount=3` arrives as an int64 and a values
file's `2` as a float64, and `gt` refuses to compare different types.

</details>

## Verification

Install the chart for real, through the Ingress, and look at what the application received:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm install web examples/basic-chart --namespace lab-05 --set ingress.enabled=true --wait --timeout 3m | head -6
```

<!-- test: retry=20; contains=APP_ENV: "dev"; output -->
```bash
curl -s http://basic.localhost:8080/config.js; echo
kubectl get pods -n lab-05 -L environment,team
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

NAME                   READY   STATUS    RESTARTS   AGE   ENVIRONMENT   TEAM
web-56c77bb496-dwstk   1/1     Running   0          4s    dev           web
web-56c77bb496-glqg8   1/1     Running   0          4s    dev           web
```

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls the release web and deletes the namespace lab-05.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall web --namespace lab-05 --wait
kubectl delete namespace lab-05 --wait=false
rm -rf labs/work/tpl
```

Next: [lab 06 · Rendering and linting](06-rendering.md).
