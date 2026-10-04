# Documentation

Concept pages. Each answers the same ten questions (what is it, why, how does it work, what problem does it solve, how
do I use it, which command, which output, what can go wrong, how to troubleshoot, where it is used in real DevOps
work) and links to the lab where its commands run. Their commands come from the tested labs; the two lesson pages
(Level 17 and Level 19) are tested themselves.

| Page | Topic |
|---|---|
| [01 · What is Helm?](01-what-is-helm.md) | Level 2: chart, release, repository, chart version vs app version |
| [02 · Charts and Chart.yaml](02-charts-and-chart-yaml.md) | chart structure, versions, packaging |
| [03 · Values](03-values.md) | defaults, precedence, environment files |
| [04 · Templates, helpers and labels](04-templates-and-helpers.md) | Go templates, functions, named templates, consistent labels |
| [05 · Rendering and linting](05-rendering-and-linting.md) | `helm template`, `helm lint`, `--dry-run=server` |
| [06 · Releases](06-releases.md) | install, status, history, `helm get`, uninstall |
| [07 · Upgrades and rollbacks](07-upgrades-and-rollbacks.md) | rolling updates, failures, rollback |
| [08 · Multiple environments](08-environments.md) | one chart, many environments |
| [09 · Repositories and OCI](09-repositories.md) | distributing and consuming charts |
| [10 · Dependencies](10-dependencies.md) | subcharts, `Chart.lock`, when (not) to use them |
| [11 · Hooks, tests and NOTES](11-hooks-and-tests.md) | lifecycle hooks, `helm test`, NOTES.txt |
| [12 · ConfigMaps and Secrets](12-configmaps-and-secrets.md) | configuration and credentials in charts |
| [13 · Security](13-security.md) | **Level 17** (tested): reviewing charts, least privilege, secrets |
| [14 · Reviewing changes (Helm diff)](14-reviewing-changes.md) | previewing upgrades, drift |
| [15 · Best practices](15-best-practices.md) | the list, and where this repository applies each |
| [16 · A production-style chart](16-production-style-chart.md) | **Level 19** (tested): the Bookshop chart's design |
| [Cheat sheet](cheat-sheet.md) | every command and construct on one page |
