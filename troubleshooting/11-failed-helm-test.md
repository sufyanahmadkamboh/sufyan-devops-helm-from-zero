# 11 · Failed Helm test

> Uses demo-app in namespace `trouble`. Time: 15 minutes.

## Break it

A working release with a passing test:

<!-- test: timeout=300; contains=Succeeded -->
```bash
helm install demo charts/demo-app --namespace trouble --create-namespace \
  -f troubleshooting/values-trouble.yaml --wait --timeout 3m > /dev/null
helm test demo --namespace trouble | grep Phase
```

During a debugging session, someone edits the configuration directly in the cluster and restarts the Pods to pick
it up:

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl patch configmap demo-demo-app --namespace trouble -p '{"data":{"APP_ENV":"prod"}}'
kubectl rollout restart deployment/demo-demo-app --namespace trouble > /dev/null
kubectl rollout status deployment/demo-demo-app --namespace trouble --timeout=120s
```

## Problem

The nightly `helm test` of the release fails, though every Pod is healthy and `helm status` says `deployed`.

## Symptoms

<!-- test: fail; timeout=300; contains=Phase:          Failed; output=tail:8 -->
```bash
helm test demo --namespace trouble --logs
```

```text
...
Phase:          Failed

POD LOGS: demo-demo-app-test-connection (check)
GET http://demo-demo-app:8080/health
{"status":"ok","service":"frontend","version":"1.0.0"}
GET http://demo-demo-app:8080/config.js (expecting APP_ENV dev)

Error: resource Pod/trouble/demo-demo-app-test-connection not ready. status: Failed, message: pod demo-demo-app-test-connection failed
```

## Investigation

A test is a script: read its log to see which step failed, then compare what the release says with what is live.

## Commands

The test's last line was `GET .../config.js (expecting APP_ENV dev)`, and there is no `test passed`: the `grep` for
`APP_ENV: "dev"` failed. What does the application serve?

<!-- test: contains=APP_ENV: "prod"; output -->
```bash
curl -s http://trouble.localhost:8080/config.js; echo
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "prod" };
```

The release was deployed with `environment: dev`. Compare Helm's record with the live objects. (`--force-conflicts`
lets the preview compute Helm's values even where another tool now owns a field; `kubectl diff` changes nothing.)

<!-- test: contains=APP_ENV; output -->
```bash
helm get manifest demo --namespace trouble \
  | kubectl diff --server-side --field-manager=helm --force-conflicts --namespace trouble -f - 2>/dev/null \
  | grep -E '^[-+] ' | grep -vE 'generation:|meta\.helm\.sh/|^-\s+annotations:$|restartedAt' || true
```

```text
-  APP_ENV: prod
+  APP_ENV: dev
```

## Output Interpretation

- The test checks that the configuration of **this release** reached the application: `APP_ENV` must equal the
  release's `environment` value. It does not: the application says `prod`.
- The diff of Helm's manifest against the cluster shows one changed field: `APP_ENV` in the ConfigMap (`-` live,
  `+` Helm's). Someone changed it outside Helm. (The `restartedAt` annotation from `kubectl rollout restart` is
  filtered out above; it is drift too.)

## Root Cause

Drift: a manual `kubectl patch` changed a Helm-managed ConfigMap. Helm does not watch objects after applying them;
the test noticed.

## Fix

Re-apply the release's state with an upgrade:

<!-- test: fail; timeout=300; contains=conflict; output=tail:2 -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml --wait
```

```text
level=WARN msg="upgrade failed" name=demo error="conflict occurred while applying object trouble/demo-demo-app /v1, Kind=ConfigMap: Apply failed with 1 conflict: conflict with \"kubectl-patch\" using v1: .data.APP_ENV"
Error: UPGRADE FAILED: conflict occurred while applying object trouble/demo-demo-app /v1, Kind=ConfigMap: Apply failed with 1 conflict: conflict with "kubectl-patch" using v1: .data.APP_ENV
```

A second problem, specific to Helm 4: it applies with **server-side apply**, which records an owner ("field manager")
for every field. `kubectl patch` made itself the owner of `data.APP_ENV`, so Helm refuses to silently overwrite
another manager's change: a conflict. Here we know the manual change was wrong, so we tell Helm to take the field
back:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml --force-conflicts --wait | grep STATUS
```

The ConfigMap says `dev` again, but the running Pods read their environment when they started, with `prod`. The chart's
`checksum/config` annotation did not change (the **rendered** ConfigMap is the same as before), so the upgrade did not
roll the Pods. Restart them once:

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl rollout restart deployment/demo-demo-app --namespace trouble > /dev/null
kubectl rollout status deployment/demo-demo-app --namespace trouble --timeout=120s
```

## Verification

<!-- test: timeout=300; retry=3; contains=test passed; output=tail:6 -->
```bash
helm test demo --namespace trouble --logs
```

```text
...

POD LOGS: demo-demo-app-test-connection (check)
GET http://demo-demo-app:8080/health
{"status":"ok","service":"frontend","version":"1.0.0"}
GET http://demo-demo-app:8080/config.js (expecting APP_ENV dev)
test passed
```

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
```

## Lesson Learned

- A failing test with healthy Pods often means **drift**: the cluster no longer matches the release. Read the test
  log, then diff `helm get manifest` against the live objects.
- Helm 4 + server-side apply: fields changed by other tools cause `conflict` errors on the next upgrade. That is a
  safety net, not a bug: decide who is right, then use `--force-conflicts` only when Helm's value should win.
- A restored ConfigMap does not restart Pods by itself; environment variables are read at container start.
- Run `helm test` on a schedule, not only after deployments: it catches changes made behind Helm's back.
