# Helm From Zero · project summary

**What:** a hands-on Helm lab that starts with an application deployed as plain Kubernetes YAML, copied for dev,
staging and production, and replaces it with one versioned chart and three short values files, then operates it
through a full release lifecycle: install, review, upgrade, test, rollback, troubleshooting.

**Problem:** teams keep per-environment copies of Kubernetes manifests: one change means N edits, copies drift apart,
nothing records what was deployed, there is no whole-application undo, and passwords end up in the files. Helm is
then learned as a list of commands instead of an engineering practice.

**Contents**
- Level 1: the Bookshop (React frontend, Node.js/Python/Go/Java APIs, PostgreSQL) as raw YAML for three environments
  (1,374 lines), deployed and measured
- 17 labs (setup, install Helm, first chart, structure, values, templates, rendering, install, upgrade, rollback,
  environments, repositories, dependencies, hooks, tests, troubleshooting, capstone), each with Break It,
  Troubleshoot It and a challenge
- 16 concept pages answering ten questions each, security and best-practice pages, a cheat sheet
- 12 troubleshooting scenarios: template syntax, wrong value, incorrect image, wrong Service selector (partial upgrade
  with an immutable selector), wrong environment values, failed upgrade (a missing service account), bad revision and rollback,
  missing ConfigMap, Secret problem, dependency problem, failed Helm test (drift and a server-side apply conflict),
  values conflict (HPA vs replicaCount); plus a read-only triage script
- 12 challenges that build one chart from an empty folder; a 19-step capstone; a 24-chapter guided course; a study
  guide PDF, a 71-term glossary, 25 interview questions; a 24-chapter video (full and silent versions)

**Engineering details**
- `charts/demo-app`: the lessons' chart (frontend), with a ConfigMap checksum annotation, a Helm test that checks the
  configured environment reached the app, per-environment values and an HPA in production
- `charts/bookshop` 1.2.0: one range-driven template for five services, helpers taking a `dict` context, `tpl` for
  release-dependent URLs, a password generated once and kept with `lookup` + `helm.sh/resource-policy: keep` (or an
  `existingSecret`), a local PostgreSQL subchart (non-root, UID 70) behind a condition, a post-install/post-upgrade
  report hook, a Helm test, NOTES, and HPA + PodDisruptionBudgets for production
- Helm 4.3 specifics covered from real runs: server-side apply (`APPLY_METHOD`), kstatus-based `--wait`,
  `--rollback-on-failure`, `--force-conflicts`, plugin verification (`--verify=false` for helm-diff from Git)
- Reviewing changes with `helm template | kubectl diff --server-side --field-manager=helm`, and drift detection with
  `helm get manifest` through the same pipeline
- `tests/mdrun.py` runs every bash block of the lessons and writes the real output back into the docs; GitHub Actions
  runs all lessons in course order on kind, lints and kubeconform-validates every chart with every values file, and
  publishes the charts to `oci://ghcr.io/sufyanahmadkamboh/charts`

**Repository:** https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero
