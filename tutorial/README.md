# Helm From Zero · The Training Course

This is the guided path through the repository, in 24 chapters. Think of it as a senior DevOps engineer sitting next to
you: we decide what to run next, read the output together, break things on purpose, and investigate them the way we
would in production.

**The commands live in the lessons, not here.** Each chapter sends you to a lesson (or part of one), tells you what to
watch for, and explains what an experienced engineer thinks when they see that output. The lessons are tested end to
end ([tests/](../tests/README.md)); the output excerpts quoted here come from those real runs. Your timestamps, Pod
names and IP addresses will differ.

| Chapter | You will | Lesson | Time |
|---|---|---|---|
| [01 · Introduction](01-introduction.md) | set up the cluster, tour the repository | [lab 00](../labs/00-setup.md) | 30 min |
| [02 · The Kubernetes YAML problem](02-the-yaml-problem.md) | deploy the Bookshop without Helm, measure the duplication | [Level 1](../environments/README.md) | 30 min |
| [03 · What is Helm?](03-what-is-helm.md) | chart, release, repository, two kinds of version | [Level 2](../docs/01-what-is-helm.md) | 20 min |
| [04 · Install Helm](04-install-helm.md) | install and check Helm 4.3 | [lab 01](../labs/01-install-helm.md) | 15 min |
| [05 · Create your first chart](05-first-chart.md) | `helm create`, install, test | [lab 02](../labs/02-first-chart.md) | 30 min |
| [06 · Understand chart structure](06-chart-structure.md) | every file of a real chart | [lab 03](../labs/03-chart-structure.md) §1–4 | 25 min |
| [07 · Chart.yaml](07-chart-yaml.md) | chart version vs app version, packaging | [lab 03](../labs/03-chart-structure.md) §5 | 20 min |
| [08 · values.yaml](08-values.md) | precedence, a silent typo, schemas | [lab 04](../labs/04-values.md) | 35 min |
| [09 · Helm templates](09-templates.md) | the dozen constructs that matter | [lab 05](../labs/05-templates.md) | 45 min |
| [10 · Render and debug templates](10-render-and-debug.md) | `helm template`, `--debug`, `--dry-run=server` | [lab 06](../labs/06-rendering.md) §1–2 | 25 min |
| [11 · Helm lint](11-helm-lint.md) | a chart with three mistakes | [lab 06](../labs/06-rendering.md) §3 | 20 min |
| [12 · Install a release](12-install-release.md) | install, `helm get`, release storage, uninstall | [lab 07](../labs/07-install-release.md) | 35 min |
| [13 · Upgrade a release](13-upgrade.md) | review a diff, upgrade, forgotten values | [lab 08](../labs/08-upgrade.md) | 35 min |
| [14 · Roll back a release](14-rollback.md) | a bad upgrade, rollback, a stuck release | [lab 09](../labs/09-rollback.md) | 40 min |
| [15 · Environment-specific values](15-environments.md) | dev, staging, prod from one chart | [lab 10](../labs/10-environments.md) | 40 min |
| [16 · Helm repositories](16-repositories.md) | review and install a public chart, publish your own | [lab 11](../labs/11-repositories.md) | 40 min |
| [17 · Chart dependencies](17-dependencies.md) | subcharts, `Chart.lock`, the Bookshop chart | [lab 12](../labs/12-dependencies.md) | 45 min |
| [18 · Helm hooks](18-hooks.md) | the five hooks, a failing hook | [lab 13](../labs/13-hooks.md) | 35 min |
| [19 · Helm tests](19-tests.md) | `helm test`, NOTES, labels, drift | [lab 14](../labs/14-tests.md) | 35 min |
| [20 · Secrets and security](20-security.md) | review charts, where secrets leak | [Level 17](../docs/13-security.md) | 35 min |
| [21 · Troubleshooting](21-troubleshooting.md) | 12 failures and a method | [troubleshooting/](../troubleshooting/README.md), [lab 15](../labs/15-troubleshooting.md) | 3 h |
| [22 · Production-style chart](22-production-chart.md) | read the Bookshop chart as a design | [Level 19](../docs/16-production-style-chart.md) | 40 min |
| [23 · Capstone](23-capstone.md) | raw YAML → chart → full lifecycle | [lab 16](../labs/16-capstone.md) | 1–4 h |
| [24 · Cleanup and final review](24-cleanup-and-review.md) | remove everything, check your skills | [cleanup](../labs/cleanup.md), [challenges](../challenges/README.md) | 60 min |

About 20 hours in total, in as many sessions as you like. Every chapter after 01 uses the same kind cluster; you can
stop Docker between sessions and the cluster comes back when Docker starts again.

## How to use it

1. Two windows: this chapter, and the lesson it sends you to.
2. Type the commands yourself, and read each one before pressing Enter.
3. Before reading the explanation of an output, look at your terminal and guess what it means.
4. When a chapter says "don't fix it yet", don't: the investigation is the lesson.
5. Keep a notebook with one line per chapter: the thing that surprised you. It becomes your runbook.
6. Each chapter ends with a checkpoint. If you cannot tick an item, go back.

Ready? [01 · Introduction](01-introduction.md).
