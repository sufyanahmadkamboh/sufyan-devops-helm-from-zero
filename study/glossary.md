# Glossary

Every term used in this course, in plain words. The link points to where it is explained or used.

| Term | Meaning |
|---|---|
| **.helmignore** | Files `helm package` leaves out of a chart archive, like `.gitignore`. [lab 03](../labs/03-chart-structure.md) |
| **_helpers.tpl** | The conventional file for named templates. Files in `templates/` starting with `_` render nothing on their own. [docs/04](../docs/04-templates-and-helpers.md) |
| **alias (dependency)** | A local name for a subchart: its objects and values use the alias (`catalog`) instead of the chart name. [lab 12](../labs/12-dependencies.md) |
| **apiVersion v2** | The chart format of Helm 3 and 4, in `Chart.yaml`; not a Kubernetes API version. [docs/02](../docs/02-charts-and-chart-yaml.md) |
| **appVersion** | The version of the application a chart deploys by default, usually the image tag. A string: quote it. [docs/01](../docs/01-what-is-helm.md) |
| **Artifact Hub** | The public catalogue of Helm charts; `helm search hub` queries it. Listing is not an endorsement. [lab 11](../labs/11-repositories.md) |
| **Base64** | An encoding of bytes as text. Secret values and Helm's release records use it; it is not encryption. [docs/13](../docs/13-security.md) |
| **Chart** | A package of Kubernetes templates, default values and metadata: a folder or a `.tgz`. [docs/02](../docs/02-charts-and-chart-yaml.md) |
| **Chart.lock** | The exact dependency versions (and digest) a chart was built with. Committed; `helm dependency build` follows it. [docs/10](../docs/10-dependencies.md) |
| **Chart version** | `version:` in `Chart.yaml`: the package's SemVer version. Changes whenever the chart's contents change. [lab 03](../labs/03-chart-structure.md) |
| **Chart.yaml** | A chart's identity: name, description, type, version, appVersion, dependencies. [docs/02](../docs/02-charts-and-chart-yaml.md) |
| **checksum/config** | A Pod annotation with a hash of the rendered ConfigMap, so configuration changes roll the Pods. [lab 03](../labs/03-chart-structure.md) |
| **condition (dependency)** | A value that switches a subchart on or off (`postgres.enabled`). [lab 12](../labs/12-dependencies.md) |
| **ConfigMap** | A Kubernetes object holding non-secret configuration. [docs/12](../docs/12-configmaps-and-secrets.md) |
| **CreateContainerConfigError** | A Pod status: a referenced ConfigMap, Secret or key is missing. [troubleshooting 08](../troubleshooting/08-missing-configmap.md) |
| **default (function)** | Returns a fallback when a value is empty: `.Values.image.tag \| default .Chart.AppVersion`. [lab 05](../labs/05-templates.md) |
| **Dependency (subchart)** | A chart included in another chart, declared in `Chart.yaml`, stored in `charts/`. [docs/10](../docs/10-dependencies.md) |
| **Drift** | A difference between what Helm applied and what runs, caused by changes outside Helm. [lab 14](../labs/14-tests.md) |
| **--dry-run=server** | Render with the real cluster, let the API server validate, create nothing. [lab 06](../labs/06-rendering.md) |
| **existingSecret** | A chart value naming a Secret created outside the chart; the chart only references it. [docs/13](../docs/13-security.md) |
| **Field manager** | The owner server-side apply records for each field. Helm 4 applies as `helm`; other owners cause conflicts. [troubleshooting 11](../troubleshooting/11-failed-helm-test.md) |
| **--force-conflicts** | Lets Helm take over fields another manager owns. Use only when Helm's value should win. [troubleshooting 11](../troubleshooting/11-failed-helm-test.md) |
| **global (values)** | The one values key every chart in a tree (parent and subcharts) can read. [docs/03](../docs/03-values.md) |
| **Helm** | The package manager for Kubernetes: charts, templating, releases. [docs/01](../docs/01-what-is-helm.md) |
| **helm-diff** | An optional plugin that shows what an upgrade would change. [docs/14](../docs/14-reviewing-changes.md) |
| **Helper (named template)** | A template defined with `define` and inserted with `include`. [docs/04](../docs/04-templates-and-helpers.md) |
| **Hook** | An object Helm runs at a lifecycle moment (`pre-install`, `post-upgrade`, ...), annotated `helm.sh/hook`. [lab 13](../labs/13-hooks.md) |
| **hook-delete-policy** | When hook objects are deleted: `before-hook-creation`, `hook-succeeded`, `hook-failed`. [lab 13](../labs/13-hooks.md) |
| **hook-weight** | The order of hooks of the same event; lower first. [lab 13](../labs/13-hooks.md) |
| **HPA** | HorizontalPodAutoscaler: owns a Deployment's replica count between min and max. [troubleshooting 12](../troubleshooting/12-values-conflict.md) |
| **Immutable field** | A field Kubernetes refuses to change after creation, such as a Deployment's selector. [troubleshooting 04](../troubleshooting/04-wrong-service-selector.md) |
| **include** | Inserts a named template's output, so it can be piped (`\| nindent 4`). [lab 05](../labs/05-templates.md) |
| **Ingress / IngressClass** | HTTP routing rules / which controller (here Traefik) implements them. [lab 00](../labs/00-setup.md) |
| **kind** | Kubernetes in Docker: each node is a container. The lab cluster. [lab 00](../labs/00-setup.md) |
| **kubeconform** | A validator for Kubernetes YAML against the API schemas; `-strict` rejects unknown fields. [lab 05](../labs/05-templates.md) |
| **Library chart** | `type: library`: only helpers for other charts; cannot be installed. [docs/02](../docs/02-charts-and-chart-yaml.md) |
| **lint** | `helm lint`: checks a chart for errors and bad practices. [lab 06](../labs/06-rendering.md) |
| **lookup** | A template function that reads an object from the cluster (empty with `helm template`). [docs/16](../docs/16-production-style-chart.md) |
| **Manifest (rendered)** | The plain YAML a chart produced for a release; `helm get manifest`. [lab 07](../labs/07-install-release.md) |
| **nindent** | Adds a newline and indents every line by N spaces; keeps included YAML in place. [lab 05](../labs/05-templates.md) |
| **NOTES.txt** | A template printed after install/upgrade and by `helm status`. [lab 14](../labs/14-tests.md) |
| **OCI registry** | A container registry (GHCR, ECR...) that also stores charts; `oci://` references. [lab 11](../labs/11-repositories.md) |
| **PDB** | PodDisruptionBudget: keeps a minimum of Pods running during voluntary disruptions. [docs/16](../docs/16-production-style-chart.md) |
| **pending-upgrade** | A release status written before an upgrade applies; left behind when the operation dies, it blocks further operations. [lab 09](../labs/09-rollback.md) |
| **podinfo** | A small, maintained demo application with a public chart, used here as a third-party chart. [lab 11](../labs/11-repositories.md) |
| **Precedence (values)** | `values.yaml` < `-f` files (later wins) < `--set`. [lab 04](../labs/04-values.md) |
| **quote** | Renders a value as a YAML string. [lab 05](../labs/05-templates.md) |
| **range** | Repeats a block for each item of a list or map. [lab 05](../labs/05-templates.md) |
| **Release** | One installed instance of a chart: name, namespace, revisions. [docs/06](../docs/06-releases.md) |
| **Release Secret** | `sh.helm.release.v1.NAME.vN`: where Helm stores each revision (chart, values, manifest). [lab 07](../labs/07-install-release.md) |
| **Repository (chart)** | An HTTP server with `index.yaml` and chart archives. [docs/09](../docs/09-repositories.md) |
| **required** | Fails rendering with a message when a value is missing. [docs/cheat-sheet](../docs/cheat-sheet.md) |
| **resource-policy: keep** | Annotation that makes `helm uninstall` leave an object (the bookshop's password Secret). [docs/16](../docs/16-production-style-chart.md) |
| **Revision** | One version of a release; every install, upgrade and rollback adds one. [lab 08](../labs/08-upgrade.md) |
| **Rollback** | `helm rollback REL N`: re-applies revision N as a new revision. Restores objects, not data. [lab 09](../labs/09-rollback.md) |
| **--rollback-on-failure** | Rolls an upgrade back automatically if it fails (Helm 3: `--atomic`). [lab 09](../labs/09-rollback.md) |
| **Selector labels** | The labels a Service and Deployment select Pods with; never change them on a live release. [docs/04](../docs/04-templates-and-helpers.md) |
| **SemVer** | MAJOR.MINOR.PATCH versioning; required for chart versions. [docs/02](../docs/02-charts-and-chart-yaml.md) |
| **Server-side apply** | Kubernetes computes the merge and tracks field owners; Helm 4's apply method. [lab 07](../labs/07-install-release.md) |
| **--set** | Command-line values, highest precedence; for one-off overrides. [docs/03](../docs/03-values.md) |
| **Subchart** | See Dependency. |
| **Template** | A manifest with Go-template placeholders, in `templates/`. [docs/04](../docs/04-templates-and-helpers.md) |
| **Test (Helm)** | A Pod annotated `helm.sh/hook: test`, run by `helm test`. [lab 14](../labs/14-tests.md) |
| **tpl** | Renders a string from values as a template (values containing `{{ .Release.Name }}`). [docs/16](../docs/16-production-style-chart.md) |
| **toYaml** | Writes a value (a map) as YAML; usually followed by `nindent`. [lab 05](../labs/05-templates.md) |
| **Traefik** | The ingress controller of the lab cluster, installed from its chart. [lab 00](../labs/00-setup.md) |
| **upgrade --install** | Installs if the release is missing, upgrades otherwise: the pipeline command. [lab 10](../labs/10-environments.md) |
| **Values** | The settings a chart accepts, defaults in `values.yaml`. [docs/03](../docs/03-values.md) |
| **values.schema.json** | A JSON Schema the merged values must satisfy, checked on lint, template, install and upgrade. [lab 04](../labs/04-values.md) |
| **--wait** | Wait until resources are ready (up to `--timeout`), so `deployed` means running. [troubleshooting 03](../troubleshooting/03-incorrect-image.md) |
| **with** | Runs a block with `.` set to a value, only if the value is set. [lab 05](../labs/05-templates.md) |
