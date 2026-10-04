# Labs

Every lab is hands-on and tested: each command in it runs in CI on a real kind cluster, and the outputs shown are
real. Each lab has the same sections: Objective, Prerequisites, Task, Commands, Expected Output, Explanation, Break It,
Troubleshoot It, Challenge, Solution, Verification, Cleanup.

| Lab | Level | You will |
|---|---|---|
| [00 · Setup](00-setup.md) | – | create the kind cluster and install Traefik |
| [01 · Install Helm](01-install-helm.md) | 3 | install Helm 4, find its configuration |
| [02 · First chart](02-first-chart.md) | 4 | `helm create`, lint, install, test, point it at your app |
| [03 · Chart structure](03-chart-structure.md) | 5 | read a chart file by file; chart version vs app version |
| [04 · Values](04-values.md) | 6 | values precedence, `--set` vs `-f`, schemas |
| [05 · Templates](05-templates.md) | 7 | every template construct used in this course |
| [06 · Render and lint](06-rendering.md) | 8 | `helm template`, `--dry-run=server`, `helm lint` |
| [07 · Install a release](07-install-release.md) | 9 | install, `helm get`, where releases live, uninstall |
| [08 · Upgrade](08-upgrade.md) | 10 | review with a diff, upgrade, rolling update, forgotten values |
| [09 · Rollback](09-rollback.md) | 11 | bad upgrade, rollback, `--rollback-on-failure`, stuck releases |
| [10 · Environments](10-environments.md) | 12 | dev, staging, prod from one chart |
| [11 · Repositories](11-repositories.md) | 13 | third-party charts, review, OCI, publishing |
| [12 · Dependencies](12-dependencies.md) | 14 | parent and child charts, `Chart.lock`, the Bookshop chart |
| [13 · Hooks](13-hooks.md) | 15 | the five common hooks, a failing hook |
| [14 · Tests](14-tests.md) | 16 | `helm test`, NOTES, labels, drift |
| [15 · Troubleshooting](15-troubleshooting.md) | 18 | a broken release with two faults, a method |
| [16 · Capstone](16-capstone.md) | 20 | raw YAML → chart → full release lifecycle |
| [Cleanup](cleanup.md) | – | remove everything, final review |

Between the labs: [Level 1 · The YAML problem](../environments/README.md), [Level 2 · What is Helm?](../docs/01-what-is-helm.md),
[Level 17 · Security](../docs/13-security.md), [the 12 troubleshooting scenarios](../troubleshooting/README.md),
[Level 19 · A production-style chart](../docs/16-production-style-chart.md).

Work files go to `labs/work/` (ignored by Git). Run a lab's commands from the repository's root folder.
