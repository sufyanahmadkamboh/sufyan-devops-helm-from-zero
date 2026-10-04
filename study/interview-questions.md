# Interview questions

25 questions that come up in interviews for DevOps, platform and cloud roles where Helm is used. Answer each one out
loud first, then open the model answer. Each answer links to the lesson where you did it yourself: in an interview,
"I did this in a lab, and here is what I saw" beats any memorised definition.

## Fundamentals

<details><summary>1. What is Helm, and what problem does it solve?</summary>

The package manager for Kubernetes. It packages an application's manifests as a versioned chart, renders them with
per-environment values, and installs them as a release with history. It solves duplication (one chart instead of a copy
of the YAML per environment), drift, missing deployment history, whole-application rollback, and distribution of
applications to other teams. ([Level 1](../environments/README.md), [docs/01](../docs/01-what-is-helm.md))
</details>

<details><summary>2. Chart version vs app version: what is the difference?</summary>

`version` is the package (templates, defaults); `appVersion` is the software deployed by default (usually the image
tag). A new template option changes the chart version only; a new application release changes `appVersion`, and the
chart version too, because the package's contents changed. Published chart versions never change contents.
([lab 03](../labs/03-chart-structure.md))
</details>

<details><summary>3. What is a release, and where does Helm store it?</summary>

One installed instance of a chart, with a name, a namespace and numbered revisions. Each revision (chart, values,
rendered manifest, status) is a Secret `sh.helm.release.v1.NAME.vN` in the release's namespace. No server component:
anyone with access to the namespace sees the same releases. ([lab 07](../labs/07-install-release.md))
</details>

<details><summary>4. Explain values precedence.</summary>

The chart's `values.yaml`, then each `-f` file in order (later wins), then `--set` (highest). Maps merge key by key,
lists are replaced, `null` deletes a key. Precedence decides a key's value, not whether a template uses it: with
autoscaling on, `replicaCount` is ignored. ([lab 04](../labs/04-values.md), [troubleshooting 12](../troubleshooting/12-values-conflict.md))
</details>

<details><summary>5. helm template vs helm install --dry-run=server?</summary>

`helm template` renders locally with no cluster: default capabilities, empty `lookup`, no validation. `--dry-run=server`
renders with the real cluster and lets the API server validate every object without creating any. Use the first in CI
and reviews, the second just before applying. ([lab 06](../labs/06-rendering.md))
</details>

## Templates

<details><summary>6. Why `nindent` and not just indentation in the template file?</summary>

Templates produce text. `include` returns a block without indentation; `nindent N` adds a newline and indents every
line, so the block lands at the right YAML level. The wrong number can even produce valid YAML with a different
structure (labels under `metadata` instead of `metadata.labels`) that lint and a server dry run accept.
([lab 05](../labs/05-templates.md#break-it))
</details>

<details><summary>7. What are helpers for, and why separate selector labels from common labels?</summary>

Named templates written once (`define`) and reused (`include`): names and labels stay identical across objects. Selector
labels go into their own helper because a Deployment's selector is immutable: adding a label there breaks upgrades and,
partially applied, can break routing. ([troubleshooting 04](../troubleshooting/04-wrong-service-selector.md))
</details>

<details><summary>8. How do you make Pods restart when only a ConfigMap changes?</summary>

Put a hash of the rendered ConfigMap into the Pod template annotations
(`checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}`). A config change changes
the Pod template, which Kubernetes rolls out. ([lab 03](../labs/03-chart-structure.md))
</details>

<details><summary>9. How would you stop users from passing invalid values?</summary>

A `values.schema.json`: Helm validates the merged values on lint, template, install and upgrade (types, minimums,
enums, required keys). Also `required` in templates, and `fail` for impossible combinations. ([lab 04](../labs/04-values.md#challenge))
</details>

## Releases and operations

<details><summary>10. An upgrade succeeded but the app disappeared. What happened?</summary>

The likeliest cause is that the upgrade was run without the environment's values files: `helm upgrade` uses only the values given in that command,
so the release fell back to defaults (here `ingress.enabled: false`, which deleted the Ingress). `helm get values` shows
it immediately. Fix by upgrading with the full set of files; prevent it with a scripted command.
([lab 08](../labs/08-upgrade.md#break-it))
</details>

<details><summary>11. Walk me through a rollback.</summary>

`helm history` to find the last good revision, optionally `helm get values/manifest --revision N` to confirm it, then
`helm rollback REL N --wait`. It creates a new revision copying N; history is never rewritten. It restores objects and
values, not data (migrations, volumes). `--rollback-on-failure` automates it for failing upgrades, but not for
"successful" bad ones. ([lab 09](../labs/09-rollback.md))
</details>

<details><summary>12. "another operation (install/upgrade/rollback) is in progress": what do you do?</summary>

A previous operation was killed after writing a `pending-*` revision (a CI runner that died, a `kill -9`, a lost machine; a polite Ctrl+C or SIGTERM lets Helm 4 mark it failed instead). Check that nothing
is really running (CI, teammates), then `helm rollback REL LAST_GOOD`, which replaces the pending state.
([lab 09](../labs/09-rollback.md#break-it))
</details>

<details><summary>13. Why always use --wait?</summary>

Without it, Helm reports `deployed` as soon as the API server accepts the objects, even if no Pod can start. With
`--wait` (and `--timeout`), Helm waits for readiness and marks the revision `failed` otherwise, which also makes
`--rollback-on-failure` and pipeline gates meaningful. ([troubleshooting 03](../troubleshooting/03-incorrect-image.md))
</details>

<details><summary>14. How do you review an upgrade before applying it?</summary>

Render the new state and diff it against the live objects with server-side apply semantics:
`helm template ... | kubectl diff --server-side --field-manager=helm -f -`, or the helm-diff plugin. Review the result,
not the values change. ([docs/14](../docs/14-reviewing-changes.md))
</details>

<details><summary>15. What does helm uninstall leave behind?</summary>

The namespace, StatefulSet volume claims, objects annotated `helm.sh/resource-policy: keep`, hook objects not removed
by their delete policy, and CRDs from `crds/`. Verify the namespace afterwards, not just `helm list`.
([lab 07](../labs/07-install-release.md))
</details>

## Environments, repositories, dependencies

<details><summary>16. How do you manage dev, staging and production with Helm?</summary>

One chart version for all; a values file per environment with only the differences; a namespace per environment; the
same command shape everywhere (`helm upgrade --install REL CHART -n app-$ENV -f values-$ENV.yaml --wait`), promotion =
the same chart version with the next file, gated by `helm test`. Secrets are referenced, never stored in values.
([lab 10](../labs/10-environments.md), [Level 19](../docs/16-production-style-chart.md))
</details>

<details><summary>17. How do you evaluate a third-party chart before installing it?</summary>

Who publishes it and is it maintained; `helm show chart/values/readme`; render it with your values and look for
cluster-wide objects (ClusterRoles, webhooks, CRDs), privileged settings and every image (including test Pods); pin the
version (or digest); review its dependencies. ([lab 11](../labs/11-repositories.md), [security](../docs/13-security.md))
</details>

<details><summary>18. HTTP chart repository vs OCI registry?</summary>

An HTTP repository serves `index.yaml` plus `.tgz` files (`helm repo add/update`, `repo/chart`). An OCI registry stores
charts as artifacts in a container registry (`helm push`, `oci://host/path/chart`), with registry authentication and
digests, without an index. ([lab 11](../labs/11-repositories.md))
</details>

<details><summary>19. dependency update vs dependency build, and what goes into Git?</summary>

`update` resolves `Chart.yaml`, downloads, and rewrites `Chart.lock`; `build` downloads exactly what the lock says.
Commit `Chart.yaml` and `Chart.lock`, not `charts/*.tgz`; CI runs `build`. ([lab 12](../labs/12-dependencies.md))
</details>

<details><summary>20. When is a subchart the wrong choice?</summary>

When the component is shared by many applications (an ingress controller), has its own owner or lifecycle, or is a
production database that needs its own backups and upgrades (often a managed service or an operator). A `condition`
lets the same chart use a bundled database in dev and an external one in production. ([docs/10](../docs/10-dependencies.md))
</details>

## Hooks, tests, security, troubleshooting

<details><summary>21. When would you use a Helm hook, and what are the risks?</summary>

For work that must happen at a precise moment of a release: a migration before the new version (`pre-upgrade`), a
report or smoke check after it (`post-upgrade`). Risks: they block the operation, a rollback does not undo their
effects, their objects survive uninstall without a delete policy, and GitOps tools translate them differently.
([lab 13](../labs/13-hooks.md))
</details>

<details><summary>22. What makes a good Helm test?</summary>

It checks what a deployment can prove (Services route to Ready Pods, dependencies reachable, this release's
configuration reached the app), runs as non-root, and really fails: `set -e`, no failures hidden inside `$( )`. Test it by
breaking what it guards. ([lab 14](../labs/14-tests.md))
</details>

<details><summary>23. How do you handle secrets in Helm charts?</summary>

Never in values files (Git) or `--set` (release record, shell history). Generate in the cluster with `lookup` and
`resource-policy: keep` for dev; reference an existing Secret by name (`existingSecret`) for production, filled by an
external secret manager (External Secrets Operator, CSI driver) or encrypted in Git (SOPS, Sealed Secrets).
([security](../docs/13-security.md))
</details>

<details><summary>24. helm upgrade fails with "conflict with kubectl-patch". Explain.</summary>

Helm 4 applies with server-side apply and records field ownership. Someone changed a field with kubectl, which now owns
it; Helm refuses to overwrite another manager's change silently. Investigate the drift (`helm get manifest | kubectl diff
--server-side --field-manager=helm -f -`), then use `--force-conflicts` if Helm's value should win.
([troubleshooting 11](../troubleshooting/11-failed-helm-test.md))
</details>

<details><summary>25. A Helm release is broken. Describe your troubleshooting method.</summary>

Triage the facts in a fixed order: `helm status`, `helm history`, `helm get values`, Pods, workloads, endpoints, warning
events (this repository's `triage.sh`). Take the first anomaly as the hypothesis, confirm it with one command
(`describe`, logs, a manifest diff), fix it in values or the chart, `helm upgrade --wait`, verify with `helm test` and
the app, and repeat: a second fault can hide behind the first. ([lab 15](../labs/15-troubleshooting.md))
</details>
