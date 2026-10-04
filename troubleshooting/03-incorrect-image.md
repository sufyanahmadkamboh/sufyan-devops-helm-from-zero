# 03 · Incorrect image

> Uses demo-app in namespace `trouble`. Time: 10 minutes.

## Break it

A new values file for a team that "renamed the image", deployed without `--wait`:

<!-- test: timeout=300; contains=STATUS: deployed; output -->
```bash
helm install demo charts/demo-app --namespace trouble --create-namespace \
  -f troubleshooting/values-trouble.yaml \
  --set image.repository=ghcr.io/sufyanahmadkamboh/bookshop-frontnd
```

```text
NAME: demo
LAST DEPLOYED: Mon Oct  5 01:07:58 2026
NAMESPACE: trouble
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
demo-app 1.0.0 (chart 1.0.0) is deployed as release "demo" in namespace "trouble".
Environment: dev · revision 1

Open:  http://trouble.localhost:8080/

Check it:
  kubectl --namespace trouble get pods -l app.kubernetes.io/instance=demo
  helm test demo --namespace trouble
```

## Problem

Helm reported `STATUS: deployed`, but `http://trouble.localhost:8080/` does not work.

## Symptoms

<!-- test: retry=10; contains=no available server; output -->
```bash
curl -s http://trouble.localhost:8080/; echo
```

```text
no available server
```

## Investigation

`deployed` only means Kubernetes **accepted** the objects: without `--wait`, Helm does not check that anything
started. Traefik's `no available server` means the Ingress and Service exist but there is no Ready Pod behind them.
So: look at the Pods.

## Commands

<!-- test: retry=20; contains=ImagePullBackOff; output -->
```bash
kubectl get pods --namespace trouble
```

```text
NAME                             READY   STATUS             RESTARTS   AGE
demo-demo-app-5b8d98bbf6-62tg8   0/1     ImagePullBackOff   0          16s
```

<!-- test: contains=bookshop-frontnd; output -->
```bash
kubectl describe pod --namespace trouble -l app.kubernetes.io/instance=demo | grep -E 'Image:|Failed|Back-off' | sort -u | head -5
```

```text
    Image:          ghcr.io/sufyanahmadkamboh/bookshop-frontnd:1.0.0
  Normal   BackOff    15s               kubelet            spec.containers{demo-app}: Back-off pulling image "ghcr.io/sufyanahmadkamboh/bookshop-frontnd:1.0.0"
  Warning  Failed     15s               kubelet            spec.containers{demo-app}: Error: ImagePullBackOff
  Warning  Failed     1s (x2 over 15s)  kubelet            spec.containers{demo-app}: Error: ErrImagePull
  Warning  Failed     1s (x2 over 15s)  kubelet            spec.containers{demo-app}: Failed to pull image "ghcr.io/sufyanahmadkamboh/bookshop-frontnd:1.0.0": failed to pull and unpack image "ghcr.io/sufyanahmadkamboh/bookshop-frontnd:1.0.0": failed to resolve reference "ghcr.io/sufyanahmadkamboh/bookshop-frontnd:1.0.0": failed to authorize: failed to fetch anonymous token: unexpected status from GET request to https://ghcr.io/token?scope=repository%3Asufyanahmadkamboh%2Fbookshop-frontnd%3Apull&service=ghcr.io: 403 Forbidden
```

<!-- test: fail; contains=waiting to start; output -->
```bash
kubectl logs --namespace trouble -l app.kubernetes.io/instance=demo
```

```text
Error from server (BadRequest): container "demo-app" in pod "demo-demo-app-5b8d98bbf6-62tg8" is waiting to start: trying and failing to pull image
```

## Output Interpretation

- `ErrImagePull` → `ImagePullBackOff`: the kubelet tried to download the image, failed, and now waits longer and
  longer between attempts.
- `describe` gives the reason: pulling `ghcr.io/sufyanahmadkamboh/bookshop-frontnd:1.0.0` failed with
  `403 Forbidden`. GHCR (like most registries) answers the same way for "does not exist" and "you may not see it", so
  a typo in a public image looks like a permission problem.
- `kubectl logs` has nothing to show: the container never started. No logs is itself a clue that the problem
  is before the application.

## Root Cause

A typo in `image.repository`: `bookshop-frontnd` instead of `bookshop-frontend`. The usual suspects for this
symptom: a wrong repository or tag, a private registry without `imagePullSecrets`, or a tag that was never pushed.

## Fix

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml --wait --timeout 3m | grep STATUS
```

## Verification

<!-- test: retry=20; contains=APP_ENV: "dev"; absent=ImagePull; absent=Terminating; output -->
```bash
kubectl get pods --namespace trouble
curl -s http://trouble.localhost:8080/config.js; echo
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
demo-demo-app-68d8b4d8dc-7hf9j   1/1     Running   0          4s
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };
```

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
```

## Lesson Learned

- `helm install` without `--wait` reports success as soon as the API server accepts the objects. Use `--wait` (and
  `--timeout`) so Helm's status means "running".
- `ImagePullBackOff` → `kubectl describe pod` → read the `Failed` events: wrong name, wrong tag, or no credentials.
- Check an image exists before deploying it: `docker manifest inspect IMAGE` or your registry's UI. In CI, render the
  chart and verify every `image:` line.
