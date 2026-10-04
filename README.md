# ⎈ Helm From Zero · Complete Hands-On Helm Learning Lab

[![test-lessons](https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero/actions/workflows/test.yaml/badge.svg)](https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero/actions/workflows/test.yaml)

Learn Helm the way it is used at work: start from an application deployed with plain Kubernetes YAML, feel the pain
of maintaining it for dev, staging and production, then replace 1,374 lines of copied YAML with a chart, three short
values files and a release history you can roll back.

```text
Raw Kubernetes YAML → understand the problem → Helm chart → templates → values → render → lint → install
  → upgrade → rollback → multiple environments → repositories → dependencies → hooks → tests → security
  → troubleshooting → production-style chart → capstone
```

**Every command is tested.** All labs, the twelve troubleshooting scenarios, the challenges and the capstone run
automatically in GitHub Actions against a real Kubernetes cluster (kind), with Helm 4.3. The outputs shown in the
lessons are real outputs of those runs.

## What is Helm?

Helm is the **package manager for Kubernetes**: it packages an application's Kubernetes manifests as a versioned
**chart**, renders them with your **values** (settings) into plain YAML, and installs them as a **release** with a
numbered history you can upgrade and roll back. [More: Level 2](docs/01-what-is-helm.md).

```text
                    Helm chart (templates: written once)
                                  │
           ┌──────────────────────┼──────────────────────┐
           ▼                      ▼                      ▼
     values-dev.yaml       values-staging.yaml     values-prod.yaml
           │                      │                      │
           └──────────────────────┼──────────────────────┘
                                  ▼
                       Kubernetes resources (a release per environment)
```

## Why do we need Helm?

The same application in three environments, without Helm, is three copies of the same YAML ([Level 1](environments/README.md)):

| Without Helm | With Helm |
|---|---|
| 458 lines per environment, 90 % identical | one chart + 3 to 32 lines of values per environment |
| one change = one edit per environment | one change in the chart, used everywhere |
| no record of what was applied | release history: every revision, its values, its manifest |
| undo = re-apply old files, if you have them | `helm rollback shop 2` |
| passwords committed next to the YAML | generated in the cluster, or referenced by name |
| other teams copy your folder | they install `bookshop --version 1.2.0` |

## What problem does this project solve?

Most Helm tutorials teach commands in isolation. This lab teaches the **engineering**: why a chart is shaped the way it
is, how to see what Helm will do before it does it, how releases fail in practice (stuck upgrades, immutable selectors,
server-side apply conflicts, drift) and how to investigate them like you would in production.

## What will I learn?

- Charts: `Chart.yaml`, **chart version vs application version**, `values.yaml`, templates, helpers, NOTES, tests
- Go templates as used in real charts: `.Values`, `.Release`, `.Chart`, `.Capabilities`, `if`, `range`, `with`,
  `default`, `quote`, `toYaml`, `nindent`, `include`, `tpl`, `lookup`
- Rendering and linting (`helm template`, `helm lint`, `--dry-run=server`, kubeconform), values schemas
- Releases: install, upgrade, rollback, uninstall, history, `helm get`, `--wait`, `--rollback-on-failure`
- Values precedence (`values.yaml` < `-f` < `--set`) and multi-environment deployments
- Reviewing changes before an upgrade (server-side diff, optional helm-diff plugin)
- Repositories, Artifact Hub, OCI registries, publishing your own chart
- Dependencies, hooks, Helm tests, ConfigMaps and Secrets, security
- Troubleshooting: 12 realistic failures and a repeatable method

## Prerequisites

You know Linux terminal basics, Docker, and Kubernetes basics (Deployments, Services, ConfigMaps, Secrets, Ingress,
kubectl). This is not a Kubernetes beginner course; if those words are new, start with
[Kubernetes From Zero](https://github.com/sufyanahmadkamboh/sufyan-devops-kubernetes-from-zero).

| Tool | Version used | Install |
|---|---|---|
| Docker | 27+ | [docs.docker.com](https://docs.docker.com/get-started/get-docker/) |
| kind | v0.33.0 | [kind.sigs.k8s.io](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) |
| kubectl | v1.37 | [kubernetes.io](https://kubernetes.io/docs/tasks/tools/) |
| Helm | **v4.3.0** | [lab 01](labs/01-install-helm.md) |
| curl, git, bash | any recent | Windows: Git Bash |

About 4 CPU cores and 8 GB of RAM free for the cluster. Internet access (images from GHCR, charts from public
repositories).

## How to start

```bash
git clone https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero.git
cd sufyan-devops-helm-from-zero
```

Then [lab 00 · Setup](labs/00-setup.md), and follow the roadmap. Run every command from the repository's root folder.
Prefer a guided path? The [tutorial](tutorial/README.md) walks through the whole course in 24 chapters; the
[study guide](study/README.md) has a glossary, interview questions and a PDF.

## Learning roadmap

| Level | Topic | Lesson |
|---|---|---|
| – | Setup: kind cluster + Traefik | [labs/00-setup](labs/00-setup.md) |
| 1 | Kubernetes YAML problem | [environments/README](environments/README.md) |
| 2 | What is Helm? | [docs/01-what-is-helm](docs/01-what-is-helm.md) |
| 3 | Install Helm | [labs/01-install-helm](labs/01-install-helm.md) |
| 4 | Create first chart | [labs/02-first-chart](labs/02-first-chart.md) |
| 5 | Chart structure | [labs/03-chart-structure](labs/03-chart-structure.md) |
| 6 | Values | [labs/04-values](labs/04-values.md) |
| 7 | Templates | [labs/05-templates](labs/05-templates.md) |
| 8 | Render & lint | [labs/06-rendering](labs/06-rendering.md) |
| 9 | Install releases | [labs/07-install-release](labs/07-install-release.md) |
| 10 | Upgrade | [labs/08-upgrade](labs/08-upgrade.md) |
| 11 | Rollback | [labs/09-rollback](labs/09-rollback.md) |
| 12 | Multiple environments | [labs/10-environments](labs/10-environments.md) |
| 13 | Repositories | [labs/11-repositories](labs/11-repositories.md) |
| 14 | Dependencies | [labs/12-dependencies](labs/12-dependencies.md) |
| 15 | Hooks | [labs/13-hooks](labs/13-hooks.md) |
| 16 | Tests | [labs/14-tests](labs/14-tests.md) |
| 17 | Security | [docs/13-security](docs/13-security.md) |
| 18 | Troubleshooting | [troubleshooting/](troubleshooting/README.md) (12 scenarios) + [labs/15-troubleshooting](labs/15-troubleshooting.md) |
| 19 | Production-style chart | [docs/16-production-style-chart](docs/16-production-style-chart.md) |
| 20 | Capstone | [labs/16-capstone](labs/16-capstone.md), then [cleanup](labs/cleanup.md) and the [challenges](challenges/README.md) |

## Repository structure

```text
helm-from-zero/
├── README.md
├── environments/            Level 1: the Bookshop as raw YAML, dev/ staging/ prod/ (the problem)
├── charts/
│   ├── demo-app/            the lessons' chart: the Bookshop frontend (values-dev/staging/prod.yaml)
│   ├── bookshop/            the production-style chart: 5 services, config, secret, ingress, hook, test, HPA/PDB
│   └── postgres/            a small PostgreSQL chart, bookshop's dependency
├── examples/
│   ├── basic-chart/         every template construct, commented (+ raw/ the YAML it replaces)
│   ├── values-example/      a chart that prints its final values: precedence made visible
│   ├── dependency-example/  a parent chart with a public dependency (podinfo, alias, condition)
│   └── hooks-example/       one Job per lifecycle hook
├── labs/                    00–16 + cleanup, each with Break It / Troubleshoot It / Challenge
├── troubleshooting/         12 scenarios + triage.sh
├── challenges/              12 challenges that build one chart step by step
├── docs/                    concept pages (10 questions each), security, best practices, cheat sheet
├── tutorial/                the course in 24 chapters
├── study/                   glossary, interview questions, study guide PDF
├── kubernetes/cluster/      kind cluster and Traefik settings
├── tests/                   mdrun.py: runs every command of the lessons
└── video/                   the video course (two versions) and its audio licenses
```

## The application

The **Bookshop** from the [Multi-Stack Applications on Kubernetes](https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes)
project: a React frontend and APIs in Node.js, Python, Go and Java, with PostgreSQL. Its images are public on GHCR
(`ghcr.io/sufyanahmadkamboh/bookshop-*:1.0.0`, and node-api `1.1.0` for the upgrade lessons), so no build step is
needed here: this project is about Helm, not about the applications.

## Versions (checked against the official sources)

| Component | Version |
|---|---|
| Helm | 4.3.0 |
| Kubernetes (kind node image) | 1.37.0 |
| kind | 0.33.0 |
| Traefik chart / Traefik | 41.6.1 / 3.7.13 |
| podinfo chart (third-party example) | 6.14.1 → 6.15.0 |
| PostgreSQL image | 18.6-alpine |

## Charts on GHCR

CI publishes the charts to GitHub's OCI registry on every push to `main`:

```bash
helm show chart oci://ghcr.io/sufyanahmadkamboh/charts/demo-app --version 1.0.0
helm show chart oci://ghcr.io/sufyanahmadkamboh/charts/bookshop --version 1.2.0
```

## License

[MIT](LICENSE). The third-party charts used in the lessons (Traefik, podinfo) keep their own licenses.
