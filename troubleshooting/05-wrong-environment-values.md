# 05 · Wrong environment values

> Uses demo-app in namespace `trouble`, which plays the **staging** environment here. Time: 10 minutes.

## Break it

Staging's values, as they should be:

<!-- test: contains=staging -->
```bash
mkdir -p labs/work
cat > labs/work/values-trouble-staging.yaml <<'EOF'
# staging on trouble.localhost
environment: staging
replicaCount: 2
config:
  adminUrl: http://admin-staging.example.com
ingress:
  enabled: true
  hosts:
    - host: trouble.localhost
      paths:
        - path: /
          pathType: Prefix
EOF
grep environment labs/work/values-trouble-staging.yaml
```

The staging deploy job was copied from the dev job, and its `-f` still points at the dev file:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade --install demo charts/demo-app --namespace trouble --create-namespace \
  -f troubleshooting/values-trouble.yaml --wait --timeout 3m | grep STATUS
```

## Problem

Deployment green. The testers report that staging "looks like dev": the footer says `dev`, the admin link is missing,
and load tests show only one replica.

## Symptoms

<!-- test: retry=20; contains=APP_ENV: "dev"; output -->
```bash
curl -s http://trouble.localhost:8080/config.js; echo
kubectl get deployment demo-demo-app --namespace trouble -L environment
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

NAME            READY   UP-TO-DATE   AVAILABLE   AGE   ENVIRONMENT
demo-demo-app   1/1     1            1           3s    dev
```

## Investigation

Nothing failed, so there is no error to read. The application runs with the configuration it was given. The
question is: **which** configuration was it given, and where did that come from?

## Commands

<!-- test: contains=environment: dev; output -->
```bash
helm get values demo --namespace trouble
```

```text
USER-SUPPLIED VALUES:
environment: dev
ingress:
  enabled: true
  hosts:
  - host: trouble.localhost
    paths:
    - path: /
      pathType: Prefix
replicaCount: 1
```

<!-- test: contains=dev; output -->
```bash
kubectl get all --namespace trouble -l app.kubernetes.io/instance=demo -L environment --no-headers | awk '{print $1, $NF}'
```

```text
pod/demo-demo-app-68d8b4d8dc-k4tt5 dev
service/demo-demo-app dev
deployment.apps/demo-demo-app dev
replicaset.apps/demo-demo-app-68d8b4d8dc dev
```

## Output Interpretation

- `helm get values` shows exactly what the deployment command supplied: the dev settings (`environment: dev`, one
  replica, no admin link). Helm did what it was told.
- The `environment` label is on every object, so a single query shows that the whole staging namespace runs dev
  configuration. This is what consistent labels are for.

## Root Cause

The wrong values file in the deployment command: `troubleshooting/values-trouble.yaml` (dev) instead of
`values-trouble-staging.yaml`. The chart has no way to know which environment a namespace is meant to be.

## Fix

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f labs/work/values-trouble-staging.yaml --wait --timeout 3m | grep STATUS
```

## Verification

<!-- test: retry=20; contains=APP_ENV: "staging"; contains=2/2; output -->
```bash
curl -s http://trouble.localhost:8080/config.js; echo
kubectl get deployment demo-demo-app --namespace trouble -L environment
```

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin-staging.example.com", APP_ENV: "staging" };

NAME            READY   UP-TO-DATE   AVAILABLE   AGE   ENVIRONMENT
demo-demo-app   2/2     2            2           7s    staging
```

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
rm -f labs/work/values-trouble-staging.yaml
```

## Lesson Learned

- A wrong configuration fails silently: no error, just the wrong behaviour. `helm get values` answers "what was this
  release deployed with?" in one command.
- Put the environment name in the configuration **and** in a label, so the mistake is visible (UI footer, `-L
  environment`).
- Generate the deployment command, don't copy it: one pipeline template with the environment as a parameter
  (`-f values-$ENV.yaml`, namespace `app-$ENV`) makes this mistake impossible to type.
- A chart can also refuse obviously wrong combinations with `fail`, for example
  `{{ if and (eq .Values.environment "dev") (hasSuffix "-prod" .Release.Namespace) }}{{ fail "dev values in a prod namespace" }}{{ end }}`.
