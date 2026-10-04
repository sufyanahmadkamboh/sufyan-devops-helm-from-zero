# 07 · Bad release revision and rollback

> Uses demo-app in namespace `trouble`. Time: 15 minutes.

## Break it

Revision 1, the install. Revision 2, a planned change (the admin link):

<!-- test: timeout=300; contains=REVISION: 2 -->
```bash
helm install demo charts/demo-app --namespace trouble --create-namespace \
  -f troubleshooting/values-trouble.yaml --wait --timeout 3m > /dev/null
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml \
  --set config.adminUrl=http://admin.example.com --wait --timeout 3m | grep REVISION
```

Revision 3: during an incident, someone "temporarily" deployed with the Ingress switched off to keep traffic away, and
forgot about it:

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml \
  --set ingress.enabled=false --wait --timeout 3m | grep STATUS
```

## Problem

Every Helm command says `deployed`, every Pod is healthy, and the application is unreachable. `--rollback-on-failure`
would not have helped: nothing failed.

## Symptoms

<!-- test: retry=10; contains=404 page not found; output -->
```bash
curl -s http://trouble.localhost:8080/; echo
helm status demo --namespace trouble | grep -E '^(STATUS|REVISION):'
```

```text
404 page not found

STATUS: deployed
REVISION: 3
```

## Investigation

This is where Helm history becomes useful. The application worked at some point: find the last revision that was
good, and what changed after it.

## Commands

<!-- test: contains=Upgrade complete; output -->
```bash
helm history demo --namespace trouble
```

```text
REVISION	UPDATED                 	STATUS    	CHART         	APP VERSION	DESCRIPTION     
1       	Mon Oct  5 01:09:44 2026	superseded	demo-app-1.0.0	1.0.0      	Install complete
2       	Mon Oct  5 01:09:45 2026	superseded	demo-app-1.0.0	1.0.0      	Upgrade complete
3       	Mon Oct  5 01:09:51 2026	deployed  	demo-app-1.0.0	1.0.0      	Upgrade complete
```

Compare the values of the last two revisions, then the objects they produced:

<!-- test: contains=enabled: false; output -->
```bash
diff <(helm get values demo --namespace trouble --revision 2) <(helm get values demo --namespace trouble --revision 3) || true
```

```text
2,3d1
< config:
<   adminUrl: http://admin.example.com
6c4
<   enabled: true
---
>   enabled: false
```

<!-- test: contains=Ingress; output -->
```bash
diff <(helm get manifest demo --namespace trouble --revision 2 | grep -E '^kind:') \
     <(helm get manifest demo --namespace trouble --revision 3 | grep -E '^kind:') || true
```

```text
5d4
< kind: Ingress
```

## Output Interpretation

- The history alone does not show the problem: three `deployed`/`superseded` revisions, all "complete". A successful
  upgrade only means Kubernetes accepted and started everything.
- The values diff: revision 3 added `ingress.enabled: false` and lost the admin link (it was a `--set` in revision 2
  and was not repeated, [lab 08](../labs/08-upgrade.md)).
- The manifest diff: revision 3 has no `Ingress` at all. Helm deleted it, as it deletes every object that disappears
  from the rendered chart.

## Root Cause

A deliberate but forgotten change, revision 3, removed the Ingress. Revision 2 is the last known-good state.

## Fix

<!-- test: timeout=300; contains=Rollback was a success -->
```bash
helm rollback demo 2 --namespace trouble --wait --timeout 3m
```

## Verification

<!-- test: retry=20; contains=admin.example.com; contains=Rollback to 2; output -->
```bash
curl -s http://trouble.localhost:8080/config.js; echo
kubectl get ingress --namespace trouble
helm history demo --namespace trouble | tail -2
```

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin.example.com", APP_ENV: "dev" };

NAME            CLASS     HOSTS               ADDRESS   PORTS   AGE
demo-demo-app   traefik   trouble.localhost             80      6s
3       	Mon Oct  5 01:09:51 2026	superseded	demo-app-1.0.0	1.0.0      	Upgrade complete
4       	Mon Oct  5 01:09:59 2026	deployed  	demo-app-1.0.0	1.0.0      	Rollback to 2   
```

The Ingress is back, and so is the admin link: a rollback restores the whole revision, values included.

<!-- test: timeout=300 -->
```bash
helm uninstall demo --namespace trouble --wait > /dev/null
```

## Lesson Learned

- "Deployed" means applied, not correct. Pair every upgrade with a check of the application itself (`helm test`, a
  smoke test in the pipeline).
- `helm get values --revision N` and `helm get manifest --revision N` diffed between revisions answer "what changed?"
  precisely.
- `helm rollback REL N` restores a revision's objects **and** values, as a new revision.
- Temporary changes need an owner and an end: put them in a reviewed values file, or don't make them through Helm.
