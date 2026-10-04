# Lab 15 · Troubleshoot a broken release

> Level 18. Time: 30 minutes. Do the [12 troubleshooting scenarios](../troubleshooting/README.md) first, or after: this
> lab trains the method, the scenarios train the individual failures.

## Objective

Bring a broken release to a working state on your own, with a repeatable method: triage, one hypothesis at a time,
fix in values (never only in the cluster), verify, repeat.

## Prerequisites

- [Lab 14](14-tests.md) and the [troubleshooting toolkit](../troubleshooting/README.md#the-investigation-toolkit).

## Task

A colleague's release `mystery` of demo-app, installed from [labs/broken-release-values.yaml](broken-release-values.yaml),
does not work. Make it work, with `helm test` passing, by changing only the values file. More than one thing may be
wrong.

## Commands

The method, in order:

```text
 1 triage      one screen of facts:            troubleshooting/triage.sh RELEASE NAMESPACE
 2 hypothesis  the first anomaly, top to bottom: status → history → values → pods → events
 3 confirm     the one command that proves it: describe, logs, get manifest, a diff
 4 fix         in the values file (or chart), then helm upgrade --wait
 5 verify      triage again; helm test; the application itself
 6 repeat      a second fault can hide behind the first
```

[triage.sh](../troubleshooting/triage.sh) is a read-only script that prints, for a release: the Helm status, the last
revisions, the user-supplied values, its Pods, workloads, Services, endpoints and the recent warning events.

## Expected Output

- After the fixes: `helm test mystery` → `Phase: Succeeded`, `http://trouble.localhost:8080/config.js` →
  `APP_ENV: "dev"`.

## Explanation

Experienced engineers are not faster because they guess better; they are faster because they look at the same few
facts in the same order every time, and change one thing at a time. A script like `triage.sh` makes the first look
cheap enough to do every time.

## Break It

Install the colleague's release exactly as they did:

<!-- test: fail; timeout=300; contains=INSTALLATION FAILED -->
```bash
helm install mystery charts/demo-app --namespace trouble --create-namespace \
  -f labs/broken-release-values.yaml --wait --timeout 60s
```

## Troubleshoot It

**Round 1 · triage.**

<!-- test: contains=ImagePull; output -->
```bash
bash troubleshooting/triage.sh mystery trouble
```

```text

== helm status
NAME: mystery
LAST DEPLOYED: Mon Oct  5 00:28:05 2026
STATUS: failed
REVISION: 1
DESCRIPTION: Release "mystery" failed: resource Deployment/trouble/mystery-demo-app not ready. status: InProgress, message: Available: 0/1

== helm history (last 3)
REVISION	UPDATED                 	STATUS	CHART         	APP VERSION	DESCRIPTION                                                             
1       	Mon Oct  5 00:28:05 2026	failed	demo-app-1.0.0	1.0.0      	Release "mystery" failed: resource Deployment/trouble/mystery-demo-app n

== values supplied by the user
USER-SUPPLIED VALUES:
containerPort: 3000
environment: dev
image:
  tag: "1.0"
ingress:
  enabled: true
  hosts:
  - host: trouble.localhost
    paths:
    - path: /
      pathType: Prefix
replicaCount: 1

== pods
NAME                               READY   STATUS         RESTARTS   AGE
mystery-demo-app-7797dc4f8-t4dlq   0/1     ErrImagePull   0          61s

== workloads and services
NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mystery-demo-app   0/1     1            0           61s

NAME                       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
service/mystery-demo-app   ClusterIP   10.96.78.138   <none>        8080/TCP   61s

NAME                                         CLASS     HOSTS               ADDRESS   PORTS   AGE
ingress.networking.k8s.io/mystery-demo-app   traefik   trouble.localhost             80      61s

== service endpoints
SERVICE            ENDPOINTS     READY
mystery-demo-app   10.244.1.61   false

== warning events of the release's objects (last 8)
mystery-demo-app-7797dc4f8-t4dlq   Failed   Failed to pull image "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0": rpc error: code = NotFound desc = failed to 
mystery-demo-app-7797dc4f8-t4dlq   Failed   Error: ErrImagePull
mystery-demo-app-7797dc4f8-t4dlq   Failed   Error: ImagePullBackOff
```

Top to bottom: status `failed`; the values contain an image tag and a container port; the Pod is in
`ErrImagePull`/`ImagePullBackOff`; the events say the image cannot be pulled. The **first** anomaly is the image:
nothing else can be judged while the container does not even start.

**Confirm:** which image, exactly?

<!-- test: contains=bookshop-frontend:1.0; output -->
```bash
kubectl get deployment mystery-demo-app --namespace trouble -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
helm show chart charts/demo-app | grep appVersion
```

```text
ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0
appVersion: 1.0.0
```

The tag `1.0` does not exist; the application's version is `1.0.0`. **Fix** in the values file (the chart's default
tag is the appVersion, so the line can simply go), and upgrade:

<!-- test: fail; timeout=300; contains=UPGRADE FAILED -->
```bash
sed -i '/^image:/,/^  tag:/d' labs/broken-release-values.yaml
helm upgrade mystery charts/demo-app --namespace trouble -f labs/broken-release-values.yaml --wait --timeout 60s
```

Still failing: there is a second fault.

**Round 2 · triage again.**

<!-- test: contains=Readiness probe failed; output -->
```bash
bash troubleshooting/triage.sh mystery trouble | sed -n '/== pods/,$p'
```

```text
== pods
NAME                                READY   STATUS             RESTARTS     AGE
mystery-demo-app-7797dc4f8-t4dlq    0/1     ImagePullBackOff   0            2m3s
mystery-demo-app-7dc6b4dddd-zwjpc   0/1     Running            2 (1s ago)   61s

== workloads and services
NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mystery-demo-app   0/1     1            0           2m3s

NAME                       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
service/mystery-demo-app   ClusterIP   10.96.78.138   <none>        8080/TCP   2m3s

NAME                                         CLASS     HOSTS               ADDRESS   PORTS   AGE
ingress.networking.k8s.io/mystery-demo-app   traefik   trouble.localhost             80      2m3s

== service endpoints
SERVICE            ENDPOINTS                 READY
mystery-demo-app   10.244.1.61,10.244.1.62   false,false

== warning events of the release's objects (last 8)
mystery-demo-app-7797dc4f8-t4dlq    Failed      Failed to pull image "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0": rpc error: code = NotFound desc = failed
mystery-demo-app-7797dc4f8-t4dlq    Failed      Error: ErrImagePull
mystery-demo-app-7797dc4f8-t4dlq    Failed      Error: ImagePullBackOff
mystery-demo-app-7dc6b4dddd-zwjpc   Unhealthy   Liveness probe failed: Get "http://10.244.1.62:3000/health": dial tcp 10.244.1.62:3000: connect: connection refu
mystery-demo-app-7dc6b4dddd-zwjpc   Unhealthy   Readiness probe failed: Get "http://10.244.1.62:3000/health": dial tcp 10.244.1.62:3000: connect: connection ref
```

The new Pod (fixed image) is `Running`; the old one keeps failing to pull until a rollout succeeds and replaces it.
But the new Pod is `0/1`, restarting, its endpoint is not ready, and its events show failing probes on port 3000. The values say `containerPort: 3000`; the frontend's nginx listens on 8080 (scenario 02). **Fix** and
upgrade:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
sed -i '/^containerPort:/d' labs/broken-release-values.yaml
helm upgrade mystery charts/demo-app --namespace trouble -f labs/broken-release-values.yaml --wait --timeout 3m | grep STATUS
```

## Challenge

Without the solution below: why was the values file still accepted by `helm lint` and `helm template` in its broken
form, and what could the chart do so that each of the two mistakes is rejected **before** anything is installed?

## Solution

<details>
<summary>Open the solution</summary>

Both values were well-formed: a string tag and an integer port. Helm cannot know that tag `1.0` does not exist or
that the application listens on 8080. Two chart-side defences:

- A `values.schema.json` ([lab 04](04-values.md)) restricting `containerPort` (`"enum": [8080]`, or a description
  that says it must match the application) and the tag format (`"pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"` rejects
  `1.0`).
- Fewer knobs: if users never need to change the container port, don't make it a value at all.

And a pipeline-side defence: check that every rendered image exists in the registry before deploying
(`helm template ... | grep image:` → `docker manifest inspect` / `crane manifest`).

</details>

## Verification

<!-- test: timeout=300; contains=Phase:          Succeeded; contains=APP_ENV: "dev"; output -->
```bash
helm test mystery --namespace trouble | grep Phase
curl -s http://trouble.localhost:8080/config.js; echo
helm history mystery --namespace trouble | cut -c1-110
```

```text
Phase:          Succeeded
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };

REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION                           
1       	Mon Oct  5 00:28:05 2026	failed    	demo-app-1.0.0	1.0.0      	Release "mystery" failed: resource Dep
        	                        	          	              	           	conte...                              
2       	Mon Oct  5 00:29:07 2026	superseded	demo-app-1.0.0	1.0.0      	Upgrade "mystery" failed: resource Dep
3       	Mon Oct  5 00:30:08 2026	deployed  	demo-app-1.0.0	1.0.0      	Upgrade complete                      
```

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls mystery, deletes the namespace trouble, restores the broken values file.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall mystery --namespace trouble --wait
kubectl delete namespace trouble --wait=false > /dev/null
git checkout -- labs/broken-release-values.yaml
```

Next, Level 19: [the production-style chart](../docs/16-production-style-chart.md).
