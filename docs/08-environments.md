# Multiple environments

> Hands-on: [lab 10](../labs/10-environments.md), [Level 19](16-production-style-chart.md).

## 1 · What is it?

One chart version deployed several times, once per environment, each release with its own values file and namespace.

## 2 · Why do we need it?

Changes must be tested in dev and staging with the same templates that will reach production; only configuration may
differ.

## 3 · How does it work?

```text
 values.yaml (defaults) + values-dev.yaml      ──► release demo in demo-dev
                        + values-staging.yaml  ──► release demo in demo-staging
                        + values-prod.yaml     ──► release demo in demo-prod
```

## 4 · What problem does it solve?

Environment drift and copy-paste (Level 1's three folders of 460 lines each).

## 5 · How do I use it?

Defaults that are safe for a laptop; one file per environment with only the differences; the same command shape for
every environment (`helm upgrade --install demo CHART -n demo-$ENV -f values-$ENV.yaml --wait`); promotion = the same
chart version with the next environment's file.

## 6 · What command should I run?

```bash
helm upgrade --install demo charts/demo-app -n demo-staging --create-namespace -f charts/demo-app/values-staging.yaml --wait
diff <(helm get values demo -n demo-staging) <(helm get values demo -n demo-prod)
kubectl get deploy -A -l app.kubernetes.io/name=demo-app -L environment
```

## 7 · What output should I expect?

The same chart version in every `helm list` row; values diffs limited to the intended differences.

## 8 · What can go wrong?

Wrong file for the environment ([05](../troubleshooting/05-wrong-environment-values.md)), wrong file order
([lab 10](../labs/10-environments.md#break-it)), environments drifting because changes were made with `--set` in one
of them.

## 9 · How do I troubleshoot it?

`helm get values` per environment and diff them; the `environment` label on every object.

## 10 · Where is it used in real DevOps work?

Environment-specific configuration: replicas, resources, hosts, ingress/TLS, feature flags, autoscaling, persistence
sizes, and **references** to secrets (never the secrets).

| Typical difference | dev | staging | prod |
|---|---|---|---|
| Replicas / autoscaling | 1 | 2 | HPA |
| Image tag | default | default | pinned |
| Resources | small | small | measured |
| Host / TLS | dev host | staging host | public host + TLS |
| Persistence | 1Gi | 2Gi | 5Gi+ |
| Secrets | generated | existing Secret | external secret manager |
