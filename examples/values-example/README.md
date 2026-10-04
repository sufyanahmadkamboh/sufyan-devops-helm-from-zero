# values-example

A chart with one template: a ConfigMap that prints the final values. Use it to predict, then check, which value wins.

```text
values.yaml            (chart defaults)        lowest priority
  ← -f team-defaults.yaml
  ← -f values-prod.yaml                          later files win over earlier ones
  ← --set key=value                              highest priority
```

```bash
helm template demo examples/values-example
helm template demo examples/values-example -f examples/values-example/team-defaults.yaml
helm template demo examples/values-example -f examples/values-example/team-defaults.yaml \
  -f examples/values-example/values-prod.yaml --set replicaCount=5
```

Used in [lab 04 · Values](../../labs/04-values.md).
