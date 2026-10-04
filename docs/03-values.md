# Values

> Hands-on: [lab 04](../labs/04-values.md), [lab 10](../labs/10-environments.md), troubleshooting
> [05](../troubleshooting/05-wrong-environment-values.md) and [12](../troubleshooting/12-values-conflict.md).

## 1 · What is it?

The settings a chart accepts. `values.yaml` holds every setting with a safe default and a comment; you override any
of them per install. Templates read them as `.Values.<key>`.

```yaml
replicaCount: 2
image:
  repository: ghcr.io/sufyanahmadkamboh/bookshop-frontend
  tag: "1.0.0"
service:
  type: ClusterIP
  port: 8080
```

## 2 · Why do we need it?

To separate **what** is deployed (templates, written once) from **how** it is configured (values, per environment).

## 3 · How does it work?

Helm merges every source into one tree, later sources overriding earlier ones:

```text
 chart's values.yaml  <  -f file1.yaml  <  -f file2.yaml  <  --set / --set-string / --set-json
```

Maps merge key by key; lists and scalars are replaced. `null` removes a key. A subchart receives the parent's values
under its name (or alias); `global:` is visible to all charts.

## 4 · What problem does it solve?

Environment differences without copies: dev, staging and prod differ by a few lines of values.

## 5 · How do I use it?

Defaults in `values.yaml`; one file per environment with only the differences; `-f` in a fixed order from a script
or pipeline; `--set` only for one-off, temporary overrides.

## 6 · What command should I run?

```bash
helm show values charts/demo-app                                  # the interface: every key and default
helm template demo charts/demo-app -f charts/demo-app/values-prod.yaml --set replicaCount=5
helm install demo charts/demo-app --dry-run=client --debug        # USER-SUPPLIED and COMPUTED VALUES
helm get values demo -n demo-dev [--all] [--revision N]           # what a release got
```

## 7 · What output should I expect?

`helm get values` prints `USER-SUPPLIED VALUES:` and only what you passed; `--all` adds the defaults.

## 8 · What can go wrong?

| Mistake | Effect |
|---|---|
| Misspelled key (`replicacount`) | silently ignored ([lab 04](../labs/04-values.md#break-it)) |
| Forgotten `-f` on upgrade | release falls back to defaults ([lab 08](../labs/08-upgrade.md#break-it)) |
| `-f values.yaml` passed last | resets every environment setting ([lab 10](../labs/10-environments.md#break-it)) |
| Unquoted numbers/booleans | wrong types (`1.10` → `1.1`, `true` instead of `"true"`) |
| Coupled values | a value that "has no effect" because another disables it ([12](../troubleshooting/12-values-conflict.md)) |
| Secrets in values | in Git and in the release record ([security](13-security.md)) |

## 9 · How do I troubleshoot it?

`helm get values` (did it arrive?) → `helm get manifest` / `helm template` (did it render?) → the template (which
condition uses it?). A `values.schema.json` turns many of these mistakes into errors at lint time.

## 10 · Where is it used in real DevOps work?

Every deployment: environment configuration in reviewed values files, kept next to the chart or in a separate
deployment repository read by CI/CD or GitOps tools.
