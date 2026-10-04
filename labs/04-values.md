# Lab 04 · Values

> Level 6. Time: 30 minutes. No cluster needed: everything is rendered with `helm template`.

## Objective

Understand why values exist, how a template reads them, and how Helm decides which value wins when the same key is
set in several places.

## Prerequisites

- [Lab 03](03-chart-structure.md).

## Task

1. Compare a hard-coded Deployment with its templated version.
2. Change values with `--set` and with `-f` files, and predict each result before you render it.
3. Find out why a value "does nothing".

## Commands

### 1 · Hard-coded vs configurable

The same Deployment, twice. Before Helm, every value is fixed in the file
([examples/basic-chart/raw/deployment.yaml](../examples/basic-chart/raw/deployment.yaml)):

<!-- test: contains=replicas: 2; output -->
```bash
grep -nE 'replicas|image:|value:' examples/basic-chart/raw/deployment.yaml
```

```text
1:# BEFORE Helm: a hard-coded Deployment. Every value below is fixed: to run 3 replicas in production, or another
10:  replicas: 2
21:          image: ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0
26:              value: dev
```

With Helm, the template has placeholders and the values have names
([examples/basic-chart/templates/deployment.yaml](../examples/basic-chart/templates/deployment.yaml)):

<!-- test: contains=.Values.replicaCount; output -->
```bash
grep -nE 'replicas|image:|value: \{\{ .Values' examples/basic-chart/templates/deployment.yaml
grep -nE '^replicaCount|^  repository|^  tag|^environment' examples/basic-chart/values.yaml
```

```text
11:  replicas: {{ .Values.replicaCount }}
25:          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
31:              value: {{ .Values.environment | quote }}
2:replicaCount: 2
5:  repository: ghcr.io/sufyanahmadkamboh/bookshop-frontend
6:  tag: ""                      # empty: "default" falls back to the chart's appVersion
8:environment: dev
```

`{{ .Values.replicaCount }}` means "the value `replicaCount` from the values". Rendering replaces each placeholder:

<!-- test: contains=replicas: 2; contains=bookshop-frontend:1.0.0; output -->
```bash
helm template web examples/basic-chart --show-only templates/deployment.yaml | grep -E 'replicas|image:|value: "dev"'
```

```text
  replicas: 2
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0"
              value: "dev"
```

Exactly the hard-coded file's values, now with names. Production is no longer a copy of the file, it is a different
value:

<!-- test: contains=replicas: 3; contains=value: "prod"; output -->
```bash
helm template web examples/basic-chart --set replicaCount=3 --set environment=prod \
  --show-only templates/deployment.yaml | grep -E 'replicas|value: "prod"'
```

```text
  replicas: 3
              value: "prod"
```

### 2 · Where values come from, and who wins

```text
 lowest   values.yaml of the chart          the defaults
   │      -f first.yaml                     a values file
   │      -f second.yaml                    a later file wins over an earlier one
 highest  --set key=value                   the command line wins over everything
```

[examples/values-example](../examples/values-example) is a chart whose only template prints the final values. Predict,
then render. Chart defaults only:

<!-- test: contains=environment: "local"; output=tail:6 -->
```bash
helm template demo examples/values-example
```

```text
...
data:
  environment: "local"
  replicaCount: "1"
  logLevel: "info"
  imageTag: "1.0.0"
  features: "{\"recommendations\":false,\"reviews\":true}"
```

Add one file, [team-defaults.yaml](../examples/values-example/team-defaults.yaml) (`logLevel: warn`,
`features.recommendations: true`):

<!-- test: contains=logLevel: "warn"; output=tail:6 -->
```bash
helm template demo examples/values-example -f examples/values-example/team-defaults.yaml
```

```text
...
data:
  environment: "local"
  replicaCount: "1"
  logLevel: "warn"
  imageTag: "1.0.0"
  features: "{\"recommendations\":true,\"reviews\":true}"
```

`features` is a map: Helm **merges** maps key by key, so `reviews: true` from the defaults survives. Now a second file,
[values-prod.yaml](../examples/values-example/values-prod.yaml) (`logLevel: error`, `replicaCount: 3`), then `--set`:

<!-- test: contains=logLevel: "error"; contains=replicaCount: "5"; output=tail:6 -->
```bash
helm template demo examples/values-example \
  -f examples/values-example/team-defaults.yaml \
  -f examples/values-example/values-prod.yaml \
  --set replicaCount=5
```

```text
...
data:
  environment: "prod"
  replicaCount: "5"
  logLevel: "error"
  imageTag: "1.0.0"
  features: "{\"recommendations\":true,\"reviews\":true}"
```

`logLevel` is set in three places: defaults `info`, team `warn`, prod `error`. The last file wins: `error`.
`replicaCount` is 3 in the prod file, but `--set` wins: 5. Reverse the order of the `-f` files and `logLevel`
becomes `warn`. **Order matters.**

### 3 · The environment files of demo-app

The real use of this mechanism: `values.yaml` holds the defaults, each environment file only what differs.

<!-- test: contains=autoscaling; output -->
```bash
cat charts/demo-app/values-prod.yaml
```

```text
# Production: pinned image version, autoscaling instead of a fixed replica count, more resources.
environment: prod
image:
  tag: "1.0.0"                 # pinned explicitly: production never follows a default
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 6
  targetCPUUtilizationPercentage: 70
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 500m
    memory: 256Mi
ingress:
  enabled: true
  hosts:
    - host: demo.localhost
      paths:
        - path: /
          pathType: Prefix
```

<!-- test: contains=HorizontalPodAutoscaler; absent=replicas:; output -->
```bash
helm template demo charts/demo-app -f charts/demo-app/values-prod.yaml | grep -E '^kind:|replicas:|minReplicas'
```

```text
kind: ServiceAccount
kind: ConfigMap
kind: Service
kind: Deployment
kind: HorizontalPodAutoscaler
  minReplicas: 3
kind: Ingress
kind: Pod
```

In production the HorizontalPodAutoscaler owns the replica count, so the Deployment has no `replicas:` field at all
(the template omits it when `autoscaling.enabled`). Values can switch whole resources on and off.

### 4 · See the merged values

To see the values a release would get, including all defaults, without installing:

<!-- test: contains=USER-SUPPLIED VALUES; contains=replicaCount: 3; output=head:16 -->
```bash
helm install demo charts/demo-app --dry-run=client --debug --set replicaCount=3 2>/dev/null | sed -n '/USER-SUPPLIED VALUES/,/COMPUTED VALUES/p'
```

```text
USER-SUPPLIED VALUES:
replicaCount: 3

COMPUTED VALUES:
```

After an install, `helm get values <release>` shows the same (lab 07).

## Expected Output

- Defaults: `environment "local"`, `replicaCount "1"`, `logLevel "info"`.
- With both files and `--set`: `environment "prod"`, `replicaCount "5"`, `logLevel "error"`, both features `true`.

## Explanation

Values separate **what** is deployed (templates, written once) from **how** it is configured (values, per
environment, per install). Rules worth memorising:

| Rule | Example |
|---|---|
| Later sources override earlier ones | `values.yaml` < `-f a.yaml` < `-f b.yaml` < `--set` |
| Maps merge, key by key | `features.recommendations` overridden, `features.reviews` kept |
| Lists are replaced as a whole | a file with `ingress.hosts: [...]` replaces the entire default list |
| `--set` is for one-off overrides | anything permanent belongs in a values file, in Git |
| `null` removes a key | `--set image.tag=null` drops prod's pinned tag: the template falls back to `appVersion` |

Prefer files over `--set`: a file is reviewed, versioned and repeatable; a long `--set` line in someone's shell
history is none of those.

## Break It

A teammate wants 3 replicas in a values file:

<!-- test: contains=replicas: 1; output -->
```bash
mkdir -p labs/work
printf 'replicacount: 3\n' > labs/work/my-values.yaml
helm template demo charts/demo-app -f labs/work/my-values.yaml --show-only templates/deployment.yaml | grep replicas
```

```text
  replicas: 1
```

Still 1, and no error.

## Troubleshoot It

Helm passes **any** key to the templates; a template only reads the keys it knows. `replicacount` is not
`replicaCount` (keys are case-sensitive), so nothing reads it. Compare your file with the chart's interface:

<!-- test: contains=replicaCount: 1; output -->
```bash
helm show values charts/demo-app | grep -i '^replica'
```

```text
replicaCount: 1
```

Fix the key, render again, and check the result rather than assuming it:

<!-- test: contains=replicas: 3 -->
```bash
printf 'replicaCount: 3\n' > labs/work/my-values.yaml
helm template demo charts/demo-app -f labs/work/my-values.yaml --show-only templates/deployment.yaml | grep replicas
```

## Challenge

Make the chart **reject** bad values instead of ignoring them: in a copy of demo-app, add a
`values.schema.json` that requires `replicaCount` to be an integer of at least 1. Prove that `--set
replicaCount=two` and `--set replicaCount=0` now fail at lint and render time.

## Solution

<details>
<summary>Open the solution</summary>

Helm validates the merged values against `values.schema.json` (JSON Schema) on lint, template, install and
upgrade:

<!-- test-run: rm -rf labs/work/schema-demo -->

<!-- test: fail; contains=want integer; output -->
```bash
cp -r charts/demo-app labs/work/schema-demo
cat > labs/work/schema-demo/values.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "replicaCount": { "type": "integer", "minimum": 1 }
  }
}
EOF
helm lint labs/work/schema-demo --set replicaCount=two
```

```text
==> Linting labs/work/schema-demo
[INFO] Chart.yaml: icon is recommended
[ERROR] values.yaml: - at '/replicaCount': got string, want integer

[ERROR] templates/: values don't meet the specifications of the schema(s) in the following chart(s):
demo-app:
- at '/replicaCount': got string, want integer


Error: 1 chart(s) linted, 1 chart(s) failed
```

<!-- test: fail; contains=minimum; output -->
```bash
helm template demo labs/work/schema-demo --set replicaCount=0
```

```text
Error: values don't meet the specifications of the schema(s) in the following chart(s):
demo-app:
- at '/replicaCount': minimum: got 0, want 1
```

A schema is the chart's contract. Many public charts ship one; `"additionalProperties": false` on an object also
catches misspelled keys like `replicacount`, at the cost of having to list every allowed key.

</details>

## Verification

<!-- test: contains=0 chart(s) failed -->
```bash
helm lint labs/work/schema-demo --set replicaCount=2
```

## Cleanup

<!-- test -->
```bash
rm -rf labs/work/schema-demo labs/work/my-values.yaml
```

Next: [lab 05 · Templates](05-templates.md).
