# Helm best practices

Each practice, with where this repository applies it.

| Practice | Why | In this repository |
|---|---|---|
| **Keep charts simple** | logic in templates is code nobody tests | plain YAML with few conditions; complexity only where it removes duplication (bookshop's `range`) |
| **Meaningful chart names** | the name becomes resource names and labels | `demo-app`, `bookshop`, `postgres` |
| **Semantic versioning** | users must trust versions | chart `1.2.0`, postgres `0.1.1` bumped when its security context changed |
| **Pin application versions** | `latest` changes under you | `appVersion` + explicit tags; prod pins `image.tag` |
| **Avoid unnecessary `--set`** | not reviewed, not repeatable, ends up in shell history and release records | environment files; overlay files for releases ([capstone](../labs/16-capstone.md)) |
| **Values files for environment configuration** | one chart, small differences | `values-dev/staging/prod.yaml` |
| **No hard-coded environment settings in templates** | templates are shared by all environments | hosts, replicas, sizes are values |
| **Keep secrets out of Git** | Git never forgets | generated Secret or `existingSecret`; nothing secret in values ([security](13-security.md)) |
| **Consistent labels** | selection, monitoring, audits | `bookshop.labels` helper on every object |
| **Reusable helpers** | one place to change names and labels | `_helpers.tpl` in every chart |
| **Validate with `helm lint`** | catches broken charts in seconds | CI lints every chart with every values file |
| **Render with `helm template`** | see what you ship | CI renders + kubeconform |
| **Test with `helm test`** | a release is not done until it works | test Pods in demo-app and bookshop |
| **Review changes before upgrades** | surprises are expensive | server-side diff ([reviewing changes](14-reviewing-changes.md)) |
| **Maintain chart documentation** | a chart is an interface | chart READMEs with value tables (`helm show readme`) |
| **Document required values** | users need to know what to set | comments in `values.yaml`; `values.schema.json` ([lab 04](../labs/04-values.md#challenge)) |
| **Avoid overusing hooks** | moving parts, leftovers, no rollback | one hook in bookshop, for a reason ([hooks](11-hooks-and-tests.md)) |
| **Keep dependencies intentional** | each one is code you run | one dependency, switchable (`postgres.enabled`), pinned, locked |
| **Always `--wait`** | `deployed` should mean running | every install and upgrade in the labs |
| **Same command shape everywhere** | prevents wrong-file mistakes | `helm upgrade --install REL CHART -n NS -f values-$ENV.yaml --wait` |
| **Selector labels never change** | Deployment selectors are immutable | separate `selectorLabels` helper ([04](../troubleshooting/04-wrong-service-selector.md)) |
| **Change via Helm only** | drift breaks upgrades (Helm 4 conflicts) and tests | [troubleshooting 11](../troubleshooting/11-failed-helm-test.md) |
