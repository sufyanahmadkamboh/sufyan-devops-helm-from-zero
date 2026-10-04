# Cleanup and final review

> Time: 5 minutes.

## What is left in the cluster

After the capstone, only the infrastructure from [lab 00](00-setup.md) should remain:

<!-- test: contains=traefik; output -->
```bash
helm list --all-namespaces
```

```text
NAME   	NAMESPACE	REVISION	UPDATED                              	STATUS  	CHART         	APP VERSION
traefik	traefik  	1       	2026-10-05 00:55:58.745498 +0200 CEST	deployed	traefik-41.6.1	v3.7.13    
```

## Level 1 · Remove Traefik, keep the cluster

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls the ingress controller; no *.localhost address will answer afterwards.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall traefik --namespace traefik --wait
kubectl delete namespace traefik --wait=false > /dev/null
```

The chart repositories you added stay in Helm's local configuration; remove them if you like:

<!-- test: contains=removed -->
```bash
helm repo remove traefik podinfo
```

## Level 2 · Delete the cluster

```text
⚠️ DESTRUCTIVE COMMAND · deletes the kind cluster helm-lab (both node containers and everything inside them).
```

<!-- test: timeout=300; contains=Deleted -->
```bash
kind delete cluster --name helm-lab 2>&1
```

<!-- test: absent=helm-lab -->
```bash
kind get clusters 2>&1
rm -rf labs/work
```

## Final review

You can now say, and show with this repository:

- **Why Helm exists:** one chart instead of a copy of the YAML per environment (Level 1: 1,374 lines → a chart and
  three short values files).
- **How charts work:** `Chart.yaml` (chart version vs app version), `values.yaml`, templates, helpers, NOTES, tests.
- **Values and templates:** precedence (`values.yaml` < `-f` files < `--set`), `if/range/with/default/quote/toYaml/
  nindent/include/tpl`, schemas.
- **Releases:** install, upgrade, rollback, uninstall, history, `helm get`, `--wait`, `--rollback-on-failure`, stuck
  releases.
- **Environments:** one chart version, a values file per environment, review with a server-side diff.
- **Repositories and dependencies:** consuming third-party charts safely, publishing to OCI, subcharts with conditions.
- **Hooks and tests:** when to use them, what they cost.
- **Security:** reviewing charts, least privilege, secrets that never touch values files or release history.
- **Troubleshooting:** a method (triage → hypothesis → confirm → fix in values → verify) and twelve failures you have
  fixed with it.

Next steps: [the challenges](../challenges/README.md), the [cheat sheet](../docs/cheat-sheet.md), and the
[interview questions](../study/interview-questions.md).
