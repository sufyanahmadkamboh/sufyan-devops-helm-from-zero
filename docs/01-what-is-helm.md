# Level 2 · What is Helm?

> Time: 15 minutes of reading. You have just seen [the YAML problem](../environments/README.md).

Helm is the **package manager for Kubernetes**. It does three jobs:

1. **Packaging:** an application's Kubernetes YAML becomes a **chart**: a folder (or a `.tgz` file) of templates and
   default settings, with a name and a version.
2. **Templating:** at install time, Helm combines the templates with **values** (your settings) and produces plain
   Kubernetes YAML.
3. **Release management:** every install of a chart is a **release**, with a name, a numbered history of
   **revisions**, a status, an upgrade path and a rollback.

```text
                    Helm
                      │
                      ▼
                    Chart
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     Chart.yaml               values.yaml   (+ your -f files and --set)
          │                       │
          └──────────┬────────────┘
                     ▼
                 templates/
                     │   helm renders on your computer
                     ▼
              Rendered YAML      (exactly what kubectl apply would get)
                     │
                     ▼
                 Kubernetes  ──►  objects + a release record (revision 1, 2, 3 ...)
```

## The vocabulary

| Term | What it is | In this repository |
|---|---|---|
| **Chart** | A package: `Chart.yaml` + `values.yaml` + `templates/` | [charts/demo-app](../charts/demo-app) |
| **Values** | The settings a chart accepts, with defaults in `values.yaml` | `replicaCount`, `image.tag`, `environment` |
| **Template** | A Kubernetes manifest with placeholders: `replicas: {{ .Values.replicaCount }}` | [deployment.yaml](../charts/demo-app/templates/deployment.yaml) |
| **Rendered manifest** | A template after Helm filled it in: plain YAML | `helm template ...` output |
| **Release** | One installed instance of a chart, with a name, in a namespace | `demo` in `demo-dev` |
| **Revision** | One version of a release; every install, upgrade, rollback adds one | `helm history demo` |
| **Repository** | A server that hosts packaged charts, with an index | `https://traefik.github.io/charts` |
| **Chart version** | The version of the **package** (`version:` in Chart.yaml) | `1.0.0` |
| **App version** | The version of the **application** it deploys (`appVersion:`) | `1.0.0` = image tag |

One chart, many releases: the same `demo-app` chart is installed three times in lab 10, as three releases (dev,
staging, prod), each with its own values and its own history.

## Chart version vs application version

The distinction that confuses most beginners. Two different things change independently:

```text
Chart.yaml
  version: 1.2.0       ← the PACKAGING. Bump it whenever anything in the chart changes:
                          a template, a default value, a new option. SemVer: 1.2.0 → 1.2.1 (fix), 1.3.0 (feature).
  appVersion: "2.0.0"  ← the APPLICATION inside. The image tag deployed by default.
```

- A new template option (say, a PodDisruptionBudget) with the same application: chart `1.2.0 → 1.3.0`,
  app stays `2.0.0`.
- The developers release `2.1.0` and nothing else changes: app `2.0.0 → 2.1.0`, and the chart version still has to
  change (`1.3.0 → 1.3.1`), because the package now has different contents. A chart version is never reused for
  different contents.

`helm list` shows both: the `CHART` column (`bookshop-1.2.0`) and the `APP VERSION` column (`1.0.0`).

## The 10 questions

**1. What is it?** A CLI that packages Kubernetes applications as charts, renders them with values, and manages
installed instances (releases) with history.

**2. Why do we need it?** Because real applications run in several environments and are installed by several teams;
copying YAML per environment does not scale (Level 1: 1,374 lines in three folders that are almost identical copies).

**3. How does it work?** The CLI loads the chart, merges values (defaults ← files ← `--set`), renders the Go templates
into YAML, sends the objects to the Kubernetes API, and stores a release record (the rendered manifest and the values
of that revision) as a Secret in the release's namespace. No component runs in the cluster.

**4. What problem does it solve?** Duplication (one template, many environments), drift (each environment is the
chart + a short values file), history (revisions and rollback), cleanup (uninstall removes what the release created),
distribution (repositories, versions) and reuse (installing other teams' charts).

**5. How do I use it?** Create or download a chart, choose values, `helm install`; later `helm upgrade`, `helm
rollback`, `helm uninstall`. Labs 02–16 do all of it.

**6. What command should I run?** `helm template` to see what would be applied, `helm upgrade --install` to apply it,
`helm history` and `helm rollback` when something goes wrong. The [cheat sheet](cheat-sheet.md) has the rest.

**7. What output should I expect?** Plain Kubernetes YAML from `helm template`; from `helm install`, a summary
(`STATUS: deployed`, `REVISION: 1`) and the chart's NOTES.

**8. What can go wrong?** Template errors (caught by `helm lint` / `helm template`), wrong values (the YAML is valid
but wrong), objects that fail in the cluster (bad image, failing probes): Helm only knows what Kubernetes reports.
[Troubleshooting](../troubleshooting/README.md) has 12 cases.

**9. How do I troubleshoot it?** Render first (`helm template`), then compare what Helm applied (`helm get manifest`,
`helm get values`) with what runs (`kubectl get/describe/logs`), then use the release history.

**10. Where is it used in real DevOps work?** Installing infrastructure (ingress controllers, cert-manager,
Prometheus: almost every one ships as a Helm chart), packaging your company's services with one chart per service or
one shared chart, deploying from CI/CD (`helm upgrade --install` in a pipeline) or from GitOps tools (Argo CD and Flux
render Helm charts).

## What Helm is not

- **Not a replacement for Kubernetes knowledge.** The output is Deployments, Services and Ingresses; when a Pod
  crashes, you debug it with kubectl, as always.
- **Not a secret manager.** A password in `values.yaml` is a password in Git ([security](13-security.md)).
- **Not the only option.** Kustomize patches plain YAML without templates (built into kubectl); it is a good fit for
  small variations of your own manifests. Helm adds packaging, versioning, distribution and release history. Many
  teams use both.

Next, Level 3: [lab 01 · Install Helm](../labs/01-install-helm.md).
