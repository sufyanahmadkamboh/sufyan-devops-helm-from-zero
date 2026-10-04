# ConfigMaps and Secrets in charts

> Hands-on: [demo-app's ConfigMap](../charts/demo-app/templates/configmap.yaml), [bookshop's Secret](../charts/bookshop/templates/secret.yaml),
> [Level 17 · Security](13-security.md), troubleshooting [08](../troubleshooting/08-missing-configmap.md) and
> [09](../troubleshooting/09-secret-problem.md).

## 1 · What is it?

Templates that render configuration (ConfigMap) and credentials (Secret) from values, and wire them into Pods
(`envFrom`, `env.valueFrom`, volumes).

## 2 · Why do we need it?

Configuration differs per environment and must reach the application; credentials must reach it without being
written where they can leak.

## 3 · How does it work?

```yaml
# ConfigMap from values
data:
  APP_ENV: {{ .Values.environment | quote }}
# Pod restarts when the configuration changes
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
# Secret: generated once, kept across upgrades, or referenced by name
{{- $existing := lookup "v1" "Secret" .Release.Namespace $name }}
```

## 4 · What problem does it solve?

Configuration as reviewed values; credentials without values.

## 5 · How do I use it?

Non-secret settings: values → ConfigMap, with a checksum annotation. Secrets: **never** as values in Git. Use one of
the safe patterns:

| Pattern | Use it for |
|---|---|
| Generated in the cluster + `lookup` + `resource-policy: keep` | dev, CI, demos |
| `existingSecret: NAME` (the chart only references it) | staging, production |
| External secret manager → Secret (External Secrets Operator, Secrets Store CSI) | production |
| Encrypted in Git (SOPS / helm-secrets, Sealed Secrets) | GitOps setups |

## 6 · What command should I run?

```bash
helm template shop charts/bookshop --set database.existingSecret=shop-db-prod | grep -c 'kind: Secret'   # 0
kubectl get secret shop-db -n bookshop-dev -o jsonpath='{.metadata.annotations}'
```

## 7 · What output should I expect?

With `existingSecret`, no Secret is rendered; the Pods reference the named one.

## 8 · What can go wrong?

Missing ConfigMap or Secret → `CreateContainerConfigError`; a Secret with the wrong value for an existing database;
passwords in values files, `--set` lines, CI logs or the release record ([security](13-security.md#5--secrets-why-values-files-are-the-wrong-place));
a changed ConfigMap that does not restart Pods (no checksum).

## 9 · How do I troubleshoot it?

`kubectl describe pod` (names the missing object), `helm get values` (the reference), `kubectl get secret/configmap`
(the object). Compare secret values by hash, never by printing them.

## 10 · Where is it used in real DevOps work?

Every application chart. Moving teams from "passwords in values files" to existing-Secret and secret-manager patterns
is a common real-world task.

## Why Helm does not make secrets secure

A Secret is base64, not encrypted; anyone with `get secrets` reads it. Helm stores every value in its release Secret,
so a password passed with `--set` is readable from the release history. Templating changes where a secret is
written, not who can read it.
